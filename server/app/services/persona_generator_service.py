import json
import logging
import re
from typing import Optional

from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from fastapi import HTTPException
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
            raise HTTPException(
                status_code=500,
                detail="LLM configuration not found. Please configure LLM settings first."
            )

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
            user_input += f"\n姓名：{request.name}"

        # 5. 运行 Agent
        try:
            result = await Runner.run(agent, user_input)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise HTTPException(
                status_code=502,
                detail=f"LLM call failed: {str(e)}"
            )
        
        # 6. 解析结果
        content = result.final_output
        if not content:
            raise HTTPException(
                status_code=502,
                detail="LLM returned empty response."
            )
        
        # 尝试解析 JSON
        parsed = PersonaGeneratorService._parse_llm_json(content)
        if not parsed:
            # 解析失败，记录原始响应到日志
            logger.error(f"Failed to parse LLM JSON response. Raw output:\n{content}")
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse LLM response as JSON. Check server logs for raw output."
            )
        
        return PersonaGenerateResponse(
            name=parsed.get("name", request.name or "未知角色"),
            description=parsed.get("description", ""),
            system_prompt=parsed.get("system_prompt", ""),
            initial_message=parsed.get("initial_message", "你好！")
        )

    @staticmethod
    def _parse_llm_json(content: str) -> Optional[dict]:
        """
        尝试从 LLM 输出中解析 JSON。
        支持以下格式：
        1. 纯 JSON
        2. Markdown 代码块包裹的 JSON (```json ... ```)
        3. 普通代码块包裹的 JSON (``` ... ```)
        """
        if not content:
            return None
        
        # 清理内容
        content = content.strip()
        
        # 按行分割
        lines = content.split('\n')
        
        # 删除首行的 ```json 或 ```
        if lines and (lines[0].strip().startswith('```json') or lines[0].strip() == '```'):
            lines = lines[1:]
        
        # 删除末行的 ```
        if lines and lines[-1].strip() == '```':
            lines = lines[:-1]
        
        # 重新组合
        json_str = '\n'.join(lines).strip()
        
        # 尝试解析
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parse failed: {e}")
            return None


persona_generator_service = PersonaGeneratorService()
