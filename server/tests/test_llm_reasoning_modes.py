import asyncio
from dataclasses import dataclass
import os

import httpx
import pytest
from agents import Agent, ModelSettings, Runner, set_default_openai_api, set_default_openai_client
from agents.items import ReasoningItem
from agents.stream_events import RunItemStreamEvent
from openai import AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
from openai.types.shared import Reasoning

from app.prompt import get_prompt
from app.services.llm_service import LLMService


@dataclass(frozen=True)
class ReasoningCase:
    name: str
    base_url_env: str
    api_key_env: str
    model_env: str
    default_base_url: str
    default_model: str


CASES = [
    ReasoningCase(
        name="openai_gpt_5_2",
        base_url_env="OPENAI_BASE_URL",
        api_key_env="OPENAI_API_KEY",
        model_env="OPENAI_MODEL_REASONING",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-5.2",
    ),
    ReasoningCase(
        name="gemini_3_flash_preview",
        base_url_env="GEMINI_BASE_URL",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="models/gemini-3-flash-preview",
    ),
    ReasoningCase(
        name="zhipu_glm_4_7",
        base_url_env="ZHIPU_BASE_URL",
        api_key_env="ZHIPU_API_KEY",
        model_env="ZHIPU_MODEL",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4.7",
    ),
]


def _resolve_case(case: ReasoningCase) -> tuple[str, str, str]:
    base_url = os.getenv(case.base_url_env) or case.default_base_url
    api_key = os.getenv(case.api_key_env)
    model_name = os.getenv(case.model_env) or case.default_model

    if not api_key:
        pytest.skip(f"Missing env for {case.name}: {case.api_key_env}")

    normalized_model = LLMService.normalize_model_name(model_name) or model_name
    return base_url, api_key, normalized_model


def _supports_sampling(model_name: str) -> bool:
    return not model_name.split("/", 1)[-1].lower().startswith("gpt-5")


async def _run_reasoning_probe(
    base_url: str,
    api_key: str,
    model_name: str,
    *,
    enable_thinking: bool,
) -> tuple[bool, bool]:
    os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        openai_client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
            http_client=http_client,
        )
        set_default_openai_client(openai_client, use_for_tracing=False)
        set_default_openai_api("chat_completions")

        model_settings_kwargs = {}
        if _supports_sampling(model_name):
            model_settings_kwargs["temperature"] = 0
            model_settings_kwargs["top_p"] = 1
        if enable_thinking:
            model_settings_kwargs["reasoning"] = Reasoning(effort="low")
        else:
            model_settings_kwargs["reasoning"] = Reasoning(effort="none")

        agent = Agent(
            name="ReasoningProbe",
            instructions="",
            model=model_name,
            model_settings=ModelSettings(**model_settings_kwargs),
        )

        prompt = get_prompt("tests/llm_test_reasoning_user_message.txt").strip()
        result = Runner.run_streamed(agent, [{"role": "user", "content": prompt}])

        reasoning_seen = False
        text_seen = False
        full_text = ""
        async for event in result.stream_events():
            if isinstance(event, RunItemStreamEvent) and event.name == "reasoning_item_created":
                if isinstance(event.item, ReasoningItem):
                    reasoning_seen = True
                continue
            if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                if event.data.delta:
                    text_seen = True
                    full_text += event.data.delta

        reasoning_tokens = 0
        if result.raw_responses:
            usage = result.raw_responses[-1].usage
            reasoning_tokens = usage.output_tokens_details.reasoning_tokens or 0

        text_has_reasoning = "<think>" in full_text.lower() or "reasoning:" in full_text.lower()
        reasoning_seen = reasoning_seen or reasoning_tokens > 0 or text_has_reasoning
        return reasoning_seen, text_seen


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_reasoning_enabled(case: ReasoningCase):
    base_url, api_key, model_name = _resolve_case(case)
    reasoning_seen, text_seen = asyncio.run(
        _run_reasoning_probe(
            base_url,
            api_key,
            model_name,
            enable_thinking=True,
        )
    )
    assert text_seen is True
    assert reasoning_seen is True


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_reasoning_disabled(case: ReasoningCase):
    base_url, api_key, model_name = _resolve_case(case)
    reasoning_seen, text_seen = asyncio.run(
        _run_reasoning_probe(
            base_url,
            api_key,
            model_name,
            enable_thinking=False,
        )
    )
    assert text_seen is True
