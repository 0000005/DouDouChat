import json
import logging
from typing import Optional

from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.models.llm import LLMConfig
from app.prompt import get_prompt
from app.schemas.persona_generator import PersonaGenerateRequest, PersonaGenerateResponse

logger = logging.getLogger(__name__)

class PersonaGeneratorService:
    @staticmethod
    async def generate_persona(
        db: Session, 
        request: PersonaGenerateRequest
    ) -> PersonaGenerateResponse:
        # 1. 获取 LLM 配置
        llm_config = (
            db.query(LLMConfig)
            .filter(LLMConfig.deleted == False)
            .order_by(LLMConfig.id.desc())
            .first()
        )
        if not llm_config:
            # 兜底：如果数据库里没有配置，可能需要抛异常或使用默认 Mock 数据
            logger.warning("LLM configuration not found. Returning mock data.")
            return PersonaGeneratorService._get_mock_persona(request)

        # 2. 设置 OpenAI 客户端
        client = AsyncOpenAI(
            base_url=llm_config.base_url,
            api_key=llm_config.api_key,
        )
        set_default_openai_client(client, use_for_tracing=False)
        set_default_openai_api("chat_completions")

        # 3. 初始化 GeneratorAgent
        instructions = get_prompt("persona/generate_instructions.txt").strip()
        
        agent = Agent(
            name="PersonaGenerator",
            instructions=instructions,
            model=llm_config.model_name,
        )

        # 4. 准备输入
        user_input = f"请为我生成一个角色。用户描述：{request.description}"
        if request.name:
            user_input += f"\n建议姓名：{request.name}"

        try:
            # 5. 运行 Agent
            result = await Runner.run(agent, user_input)
            
            # 6. 解析结果
            # 尝试从 final_output 中解析 JSON
            content = result.final_output
            # 处理可能的 Markdown 代码块
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            data = json.loads(content)
            
            return PersonaGenerateResponse(
                name=data.get("name", request.name or "未知角色"),
                description=data.get("description", ""),
                system_prompt=data.get("system_prompt", ""),
                initial_message=data.get("initial_message", "你好！")
            )
        except Exception as e:
            logger.error(f"Failed to generate persona via LLM: {e}")
            return PersonaGeneratorService._get_mock_persona(request)

    @staticmethod
    def _get_mock_persona(request: PersonaGenerateRequest) -> PersonaGenerateResponse:
        """
        Mock 实现：在 LLM 不可用时提供兜底数据。
        """
        name = request.name or request.description[:10]
        return PersonaGenerateResponse(
            name=name,
            description=f"关于 {name} 的描述",
            system_prompt=f"你现在扮演 {name}。你的描述是：{request.description}。",
            initial_message=f"你好，我是{name}，很高兴见到你！"
        )

persona_generator_service = PersonaGeneratorService()
