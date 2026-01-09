"""
Unit tests for PersonaGeneratorService.
Tests cover:
1. Mock fallback when LLM config is missing
2. Mock fallback when LLM call fails
3. Successful persona generation (mocked LLM response)
4. API endpoint integration test
"""
import json
import pytest
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.llm import LLMConfig
from app.schemas.persona_generator import PersonaGenerateRequest, PersonaGenerateResponse
from app.services.persona_generator_service import PersonaGeneratorService, persona_generator_service


pytest_plugins = ("pytest_asyncio",)

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestMockPersona:
    """Test the mock/fallback persona generation."""

    def test_mock_persona_with_name(self):
        """Test mock persona generation when name is provided."""
        request = PersonaGenerateRequest(
            description="一个像乔布斯一样的产品经理",
            name="Steve"
        )
        result = PersonaGeneratorService._get_mock_persona(request)
        
        assert isinstance(result, PersonaGenerateResponse)
        assert result.name == "Steve"
        assert "Steve" in result.description
        assert "乔布斯" in result.system_prompt
        assert "Steve" in result.initial_message

    def test_mock_persona_without_name(self):
        """Test mock persona generation when name is not provided."""
        request = PersonaGenerateRequest(description="傲娇猫娘")
        result = PersonaGeneratorService._get_mock_persona(request)
        
        assert isinstance(result, PersonaGenerateResponse)
        # Name should be derived from description (first 10 chars)
        assert result.name == "傲娇猫娘"
        assert "傲娇猫娘" in result.system_prompt

    def test_mock_persona_long_description(self):
        """Test mock persona with description longer than 10 chars."""
        request = PersonaGenerateRequest(
            description="这是一个非常非常长的角色描述，超过十个字符"
        )
        result = PersonaGeneratorService._get_mock_persona(request)
        
        # Name should be truncated to 10 chars
        assert len(result.name) == 10
        assert result.name == "这是一个非常非常长的"


@pytest.mark.asyncio
class TestPersonaGeneratorService:
    """Test the PersonaGeneratorService with mocked LLM."""

    async def test_generate_persona_no_llm_config(self, db):
        """Test that mock data is returned when no LLM config exists."""
        # Ensure no LLM config in database
        db.query(LLMConfig).delete()
        db.commit()
        
        request = PersonaGenerateRequest(description="测试角色")
        result = await PersonaGeneratorService.generate_persona(db, request)
        
        assert isinstance(result, PersonaGenerateResponse)
        # Should return mock data
        assert "测试角色" in result.system_prompt

    async def test_generate_persona_llm_success(self, db):
        """Test successful persona generation with mocked LLM response."""
        # Setup LLM config
        llm_config = LLMConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model_name="gpt-4"
        )
        db.add(llm_config)
        db.commit()
        
        # Mock LLM response
        mock_llm_response = {
            "name": "乔布斯先生",
            "description": "追求极致、改变世界的科技布道者",
            "system_prompt": "你是乔布斯，一个追求完美的产品经理...",
            "initial_message": "Stay hungry, stay foolish."
        }
        
        mock_result = SimpleNamespace(
            final_output=json.dumps(mock_llm_response, ensure_ascii=False)
        )
        
        with patch("app.services.persona_generator_service.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            
            request = PersonaGenerateRequest(
                description="一个像乔布斯一样的产品经理"
            )
            result = await PersonaGeneratorService.generate_persona(db, request)
        
        assert isinstance(result, PersonaGenerateResponse)
        assert result.name == "乔布斯先生"
        assert result.description == "追求极致、改变世界的科技布道者"
        assert "乔布斯" in result.system_prompt
        assert "Stay hungry" in result.initial_message

    async def test_generate_persona_llm_returns_markdown(self, db):
        """Test parsing LLM response wrapped in markdown code blocks."""
        # Setup LLM config
        llm_config = LLMConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model_name="gpt-4"
        )
        db.add(llm_config)
        db.commit()
        
        # Mock LLM response with markdown wrapper
        mock_json = {
            "name": "猫娘小雪",
            "description": "一个傲娇的猫娘",
            "system_prompt": "你是一个傲娇的猫娘...",
            "initial_message": "哼，主人你来了喵~"
        }
        markdown_response = f"```json\n{json.dumps(mock_json, ensure_ascii=False)}\n```"
        
        mock_result = SimpleNamespace(final_output=markdown_response)
        
        with patch("app.services.persona_generator_service.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            
            request = PersonaGenerateRequest(description="傲娇猫娘")
            result = await PersonaGeneratorService.generate_persona(db, request)
        
        assert result.name == "猫娘小雪"
        assert "猫娘" in result.system_prompt

    async def test_generate_persona_llm_exception_fallback(self, db):
        """Test that mock data is returned when LLM call fails."""
        # Setup LLM config
        llm_config = LLMConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model_name="gpt-4"
        )
        db.add(llm_config)
        db.commit()
        
        with patch("app.services.persona_generator_service.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.side_effect = Exception("LLM API error")
            
            request = PersonaGenerateRequest(
                description="测试角色",
                name="TestName"
            )
            result = await PersonaGeneratorService.generate_persona(db, request)
        
        # Should fallback to mock
        assert isinstance(result, PersonaGenerateResponse)
        assert result.name == "TestName"

    async def test_generate_persona_invalid_json_fallback(self, db):
        """Test fallback when LLM returns invalid JSON."""
        # Setup LLM config
        llm_config = LLMConfig(
            base_url="https://api.example.com",
            api_key="test-key",
            model_name="gpt-4"
        )
        db.add(llm_config)
        db.commit()
        
        mock_result = SimpleNamespace(final_output="This is not valid JSON")
        
        with patch("app.services.persona_generator_service.Runner.run", new_callable=AsyncMock) as mock_run:
            mock_run.return_value = mock_result
            
            request = PersonaGenerateRequest(description="无效响应测试")
            result = await PersonaGeneratorService.generate_persona(db, request)
        
        # Should fallback to mock
        assert isinstance(result, PersonaGenerateResponse)
        assert "无效响应测试" in result.system_prompt


@pytest.mark.asyncio
class TestPersonaGeneratorAPI:
    """Test the API endpoint integration."""

    async def test_api_endpoint_exists(self):
        """Verify the API endpoint is registered."""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Check that the route exists in the app
        routes = [route.path for route in app.routes]
        # The actual path includes the API prefix
        assert any("/friend-templates/generate" in route for route in routes)
