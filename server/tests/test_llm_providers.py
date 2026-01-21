from dataclasses import dataclass
import os

import pytest

from app.api.endpoints.llm import _test_llm_config_payload


@dataclass(frozen=True)
class ProviderCase:
    name: str
    base_url_env: str
    api_key_env: str
    model_env: str
    default_base_url: str
    default_model: str


CASES = [
    ProviderCase(
        name="openai_gpt_5_2",
        base_url_env="OPENAI_BASE_URL",
        api_key_env="OPENAI_API_KEY",
        model_env="OPENAI_MODEL_REASONING",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-5.2",
    ),
    ProviderCase(
        name="openai_gpt_4_1_nano",
        base_url_env="OPENAI_BASE_URL",
        api_key_env="OPENAI_API_KEY",
        model_env="OPENAI_MODEL_STANDARD",
        default_base_url="https://api.openai.com/v1",
        default_model="gpt-4.1-nano",
    ),
    ProviderCase(
        name="gemini_3_flash_preview",
        base_url_env="GEMINI_BASE_URL",
        api_key_env="GEMINI_API_KEY",
        model_env="GEMINI_MODEL",
        default_base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="models/gemini-3-flash-preview",
    ),
    ProviderCase(
        name="modelscope_qwen3_235b_a22b",
        base_url_env="MODELSCOPE_BASE_URL",
        api_key_env="MODELSCOPE_API_KEY",
        model_env="MODELSCOPE_MODEL",
        default_base_url="https://api-inference.modelscope.cn/v1",
        default_model="Qwen/Qwen3-235B-A22B-Instruct-2507",
    ),
    ProviderCase(
        name="minimax_m2_1",
        base_url_env="MINIMAX_BASE_URL",
        api_key_env="MINIMAX_API_KEY",
        model_env="MINIMAX_MODEL",
        default_base_url="https://api.minimax.chat/v1",
        default_model="MiniMax-M2.1",
    ),
    ProviderCase(
        name="zhipu_glm_4_7",
        base_url_env="ZHIPU_BASE_URL",
        api_key_env="ZHIPU_API_KEY",
        model_env="ZHIPU_MODEL",
        default_base_url="https://open.bigmodel.cn/api/paas/v4",
        default_model="glm-4.7",
    ),
    ProviderCase(
        name="deepseek_chat",
        base_url_env="DEEPSEEK_BASE_URL",
        api_key_env="DEEPSEEK_API_KEY",
        model_env="DEEPSEEK_MODEL",
        default_base_url="https://api.deepseek.com/v1",
        default_model="deepseek-chat",
    ),
]


def _resolve_case(case: ProviderCase) -> tuple[str, str, str]:
    base_url = os.getenv(case.base_url_env) or case.default_base_url
    api_key = os.getenv(case.api_key_env)
    model_name = os.getenv(case.model_env) or case.default_model

    missing = []
    if not api_key:
        missing.append(case.api_key_env)
    if missing:
        pytest.skip(f"Missing env for {case.name}: {', '.join(missing)}")

    return base_url, api_key, model_name


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.name)
def test_provider_chat_completion(case: ProviderCase):
    base_url, api_key, model_name = _resolve_case(case)
    result = _test_llm_config_payload(
        base_url=base_url,
        api_key=api_key,
        model_name=model_name,
    )
    assert result.get("success") is True
    assert result.get("model")
    assert result.get("response")
