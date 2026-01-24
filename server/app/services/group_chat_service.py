import json
import logging
import asyncio
from typing import List, Optional, AsyncGenerator
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models.group import Group, GroupMember, GroupMessage
from app.models.friend import Friend
from app.schemas import group as group_schemas
from app.services.llm_service import llm_service
from app.services.settings_service import SettingsService
from app.services import provider_rules
from app.prompt import get_prompt
from app.db.session import SessionLocal
from app.services.memo.constants import DEFAULT_USER_ID

from openai import AsyncOpenAI
from openai.types.shared import Reasoning
from openai.types.responses import (
    ResponseOutputText,
    ResponseTextDeltaEvent,
)
from agents import Agent, ModelSettings, RunConfig, Runner, set_default_openai_client, set_default_openai_api
from agents.items import MessageOutputItem, ReasoningItem, ToolCallItem, ToolCallOutputItem
from agents.stream_events import RunItemStreamEvent

logger = logging.getLogger(__name__)

def _model_base_name(model_name: Optional[str]) -> str:
    if not model_name:
        return ""
    return model_name.split("/", 1)[-1].lower()

def _supports_sampling(model_name: Optional[str]) -> bool:
    return not _model_base_name(model_name).startswith("gpt-5")

def _extract_reasoning_text(raw: object) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw

    def _collect_text(value: object) -> List[str]:
        texts: List[str] = []
        if not value:
            return texts
        if isinstance(value, (list, tuple)):
            for entry in value:
                texts.extend(_collect_text(entry))
            return texts
        if isinstance(value, dict):
            text = value.get("text") or value.get("content")
            if text:
                texts.append(str(text))
            return texts
        text = getattr(value, "text", None) or getattr(value, "content", None)
        if text:
            texts.append(str(text))
        return texts

    if isinstance(raw, dict):
        text = raw.get("reasoning_content") or raw.get("reasoning") or raw.get("text")
        if text:
            return str(text)
        content = raw.get("content")
        summary = raw.get("summary")
    else:
        text = getattr(raw, "reasoning_content", None) or getattr(raw, "reasoning", None) or getattr(raw, "text", None)
        if text:
            return str(text)
        content = getattr(raw, "content", None)
        summary = getattr(raw, "summary", None)

    texts = _collect_text(content)
    if not texts:
        texts = _collect_text(summary)
    return "\n".join([t for t in texts if t])

class GroupChatService:
    @staticmethod
    async def send_group_message_stream(
        db: Session, 
        group_id: int, 
        message_in: group_schemas.GroupMessageCreate,
        sender_id: str = DEFAULT_USER_ID
    ) -> AsyncGenerator[dict, None]:
        """
        发送群聊消息并获取 AI 响应。
        支持 @提及 强制触发。
        """
        # 1. 保存用户消息
        db_message = GroupMessage(
            group_id=group_id,
            sender_id=sender_id,
            sender_type="user",
            content=message_in.content,
            message_type=message_in.message_type,
            mentions=message_in.mentions
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # 发送起始事件
        yield {"event": "start", "data": {"message_id": db_message.id, "group_id": group_id}}

        # 2. 确定哪些 AI 需要回复
        # 回复逻辑：
        # a. 被 @ 的 AI 必须回复（无视 auto_reply）
        # b. 如果没有被 @ 的 AI，且群组开启了 auto_reply，则由系统决定（目前简单实现：所有 AI 都有概率回复，或者仅第一个 AI 回复）
        # c. 暂定：如果没有 @，且 auto_reply 开启，则默认群内第一个 AI 回复
        
        group = db.query(Group).filter(Group.id == group_id).first()
        if not group:
            yield {"event": "error", "data": {"detail": "Group not found"}}
            return

        participants = []
        if message_in.mentions:
            # 找到被提到的好友
            for mention_id in message_in.mentions:
                try:
                    f_id = int(mention_id)
                    friend = db.query(Friend).filter(Friend.id == f_id).first()
                    if friend:
                        participants.append(friend)
                except (ValueError, TypeError):
                    continue
        elif group.auto_reply:
            # 找到群内所有好友，任选一个回复（或根据某种逻辑选择）
            ai_members = db.query(GroupMember).filter(
                GroupMember.group_id == group_id, 
                GroupMember.member_type == "friend"
            ).all()
            if ai_members:
                # 简单起见，取第一个
                try:
                    f_id = int(ai_members[0].member_id)
                    friend = db.query(Friend).filter(Friend.id == f_id).first()
                    if friend:
                        participants.append(friend)
                except (ValueError, TypeError):
                    pass

        if not participants:
            yield {"event": "done", "data": {"message": "No AI responded"}}
            return

        # 并行运行所有 AI 的回复生成
        queue = asyncio.Queue()

        async def producer(friend_obj):
            async for event in GroupChatService._generate_ai_response(
                group_id=group_id,
                friend=friend_obj,
                user_content=message_in.content,
                history_limit=15
            ):
                await queue.put(event)

        # 启动所有后台任务
        task_list = [asyncio.create_task(producer(f)) for f in participants]

        # 消费者：将队列中的事件 yield 出去
        active_tasks = len(task_list)
        while active_tasks > 0:
            # 检查是否有任务完成
            for i, task in enumerate(task_list):
                if task and task.done():
                    try:
                        task.result() # 检查是否有异常
                    except Exception as e:
                        logger.error(f"Error in AI task: {e}")
                    task_list[i] = None
                    active_tasks -= 1

            # 消费队列中的消息
            while not queue.empty():
                yield await queue.get()
            
            if active_tasks > 0:
                await asyncio.sleep(0.05) # 稍微等待

        # 最后再排空一次队列
        while not queue.empty():
            yield await queue.get()

    @staticmethod
    async def _generate_ai_response(
        group_id: int,
        friend: Friend,
        user_content: str,
        history_limit: int = 15
    ) -> AsyncGenerator[dict, None]:
        """
        为单个 AI 生成群聊回复的生成器。
        """
        db = SessionLocal()
        try:
            # 获取上下文
            history = db.query(GroupMessage).filter(
                GroupMessage.group_id == group_id
            ).order_by(GroupMessage.create_time.desc()).limit(history_limit).all()
            history.reverse()

            # 获取参与者名称
            # 这里的参与者包括历史消息的发送者
            member_ids = {msg.sender_id for msg in history}
            # 这里的 member_ids 是字符串
            friend_ids = []
            for mid in member_ids:
                try:
                    friend_ids.append(int(mid))
                except (ValueError, TypeError):
                    continue
            
            friends_data = db.query(Friend).filter(Friend.id.in_(friend_ids)).all()
            name_map = {str(f.id): f.name for f in friends_data}
            name_map[DEFAULT_USER_ID] = "我" # 默认当前用户名为“我”
            
            # 1. Prepare LLM Config
            llm_config = llm_service.get_active_config(db)
            if not llm_config:
                yield {"event": "error", "data": {"detail": f"LLM Config missing for {friend.name}"}}
                return

            raw_model_name = llm_config.model_name
            model_name = provider_rules.normalize_llm_model_name(raw_model_name)
            
            # 2. 构建 Prompt
            system_prompt = friend.system_prompt or get_prompt("chat/default_system_prompt.txt")
            # 增加群聊上下文提示
            system_prompt += f"\n\n你现在在群聊中，你的名字是 {friend.name}。请简洁回复，避免长篇大论。如果用户提到了其他人，请根据情况互动。"

            agent_messages = []
            for msg in history:
                role = "user" if msg.sender_type == "user" else "assistant"
                # 在群聊中，内容前方加上发送者名称以便 AI 区分
                # 如果是 AI 自己发的消息，角色应为 assistant
                if msg.sender_type == "friend" and msg.sender_id == str(friend.id):
                    agent_messages.append({"role": "assistant", "content": msg.content})
                else:
                    sender_name = name_map.get(msg.sender_id, "未知")
                    agent_messages.append({"role": "user", "content": f"{sender_name}: {msg.content}"})

            # 3. Setup Agent
            client = AsyncOpenAI(base_url=llm_config.base_url, api_key=llm_config.api_key)
            set_default_openai_client(client, use_for_tracing=True)
            set_default_openai_api("chat_completions")

            temperature = friend.temperature if friend and friend.temperature is not None else 0.8
            top_p = friend.top_p if friend and friend.top_p is not None else 0.9

            use_litellm = provider_rules.should_use_litellm(llm_config, raw_model_name)
            model_settings_kwargs = {}
            if _supports_sampling(model_name):
                model_settings_kwargs["temperature"] = temperature
                model_settings_kwargs["top_p"] = top_p
            
            # 群聊通常不需要过于复杂的思考，但如果支持，可以开启
            enable_thinking = True # 默认开启
            if (
                llm_config.capability_reasoning
                and not use_litellm
                and provider_rules.supports_reasoning_effort(llm_config)
            ):
                model_settings_kwargs["reasoning"] = Reasoning(
                    effort="low" if enable_thinking else "none"
                )
            if use_litellm and enable_thinking:
                model_settings_kwargs["reasoning"] = Reasoning(effort="low")
            
            model_settings = ModelSettings(**model_settings_kwargs)
            
            if use_litellm:
                from agents.extensions.models.litellm_model import LitellmModel
                gemini_model_name = provider_rules.normalize_gemini_model_name(raw_model_name)
                gemini_base_url = provider_rules.normalize_gemini_base_url(llm_config.base_url)
                agent_model = LitellmModel(
                    model=gemini_model_name,
                    base_url=gemini_base_url,
                    api_key=llm_config.api_key,
                )
            else:
                agent_model = model_name

            agent = Agent(
                name=friend.name,
                instructions=system_prompt,
                model=agent_model,
                model_settings=model_settings,
            )

            # 4. Invoke LLM and save results
            content_buffer = ""
            assistant_msg_id = None
            
            # 先创建一个数据库消息占位
            db_msg = GroupMessage(
                group_id=group_id,
                sender_id=str(friend.id),
                sender_type="friend",
                content="",
                message_type="text"
            )
            db.add(db_msg)
            db.commit()
            db.refresh(db_msg)
            assistant_msg_id = db_msg.id

            result = Runner.run_streamed(
                agent,
                agent_messages,
                run_config=RunConfig(trace_include_sensitive_data=True),
            )

            async for event in result.stream_events():
                # 处理思考过程
                if isinstance(event, RunItemStreamEvent) and event.name == "reasoning_item_created":
                    if enable_thinking and isinstance(event.item, ReasoningItem):
                        raw = event.item.raw_item
                        text = _extract_reasoning_text(raw)
                        if text:
                            yield {
                                "event": "thinking", 
                                "data": {
                                    "delta": text,
                                    "sender_id": str(friend.id)
                                }
                            }
                    continue
                
                # 处理文本内容
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    if delta:
                        content_buffer += delta
                        yield {
                            "event": "message", 
                            "data": {
                                "delta": delta, 
                                "sender_id": str(friend.id),
                                "message_id": assistant_msg_id
                            }
                        }

            # 更新数据库
            db_msg.content = content_buffer
            db.commit()

            yield {
                "event": "done", 
                "data": {
                    "sender_id": str(friend.id),
                    "message_id": assistant_msg_id,
                    "content": content_buffer
                }
            }

        finally:
            db.close()

group_chat_service = GroupChatService()
