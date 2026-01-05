import pytest
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.services.memo.bridge import MemoServiceException
from app.vendor.memobase_server.models.response import (
    UserProfilesData, ProfileConfigData, IdsData, ProfileData
)
from app.services.memo.constants import DEFAULT_USER_ID, DEFAULT_SPACE_ID

@pytest.fixture
def mock_memo_service():
    # Patch the MemoService in the endpoints module
    with patch("app.api.endpoints.profile.MemoService", autospec=True) as mock:
        # Mock the async methods explicitly
        mock.get_profile_config = AsyncMock()
        mock.update_profile_config = AsyncMock()
        mock.get_user_profiles = AsyncMock()
        mock.add_user_profiles = AsyncMock()
        mock.update_user_profiles = AsyncMock()
        mock.delete_user_profiles = AsyncMock()
        mock.ensure_user = AsyncMock()
        yield mock

# Helper to reset global state if needed
@pytest.fixture(autouse=True)
def reset_initialization_flag():
    import app.api.endpoints.profile as profile_module
    profile_module._INITIALIZED = False
    yield
    profile_module._INITIALIZED = False

def test_get_profile_config_success(client: TestClient, mock_memo_service):
    """Test retrieving profile configuration successfully."""
    mock_memo_service.get_profile_config.return_value = ProfileConfigData(
        profile_config="topic: Test\nsub_topic: Test"
    )
    
    response = client.get("/api/memory/config")
    
    assert response.status_code == 200
    assert response.json()["profile_config"] == "topic: Test\nsub_topic: Test"
    mock_memo_service.get_profile_config.assert_called_once_with(DEFAULT_SPACE_ID)

def test_get_profile_config_failure(client: TestClient, mock_memo_service):
    """Test error handling when retrieving profile configuration fails."""
    mock_memo_service.get_profile_config.side_effect = MemoServiceException("SDK Error")
    
    response = client.get("/api/memory/config")
    
    assert response.status_code == 400
    assert "SDK Error" in response.json()["detail"]

def test_update_profile_config_success(client: TestClient, mock_memo_service):
    """Test updating profile configuration successfully."""
    mock_memo_service.update_profile_config.return_value = None
    
    response = client.put("/api/memory/config", json={"profile_config": "new config"})
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_memo_service.update_profile_config.assert_called_once_with(DEFAULT_SPACE_ID, "new config")

def test_get_profiles_success(client: TestClient, mock_memo_service):
    """Test retrieving profile list successfully."""
    test_id = uuid.uuid4()
    mock_memo_service.get_user_profiles.return_value = UserProfilesData(
        profiles=[ProfileData(id=test_id, content="Fact 1", attributes={"topic": "T1", "sub_topic": "S1"})]
    )
    
    response = client.get("/api/memory/profiles")
    
    assert response.status_code == 200
    data = response.json()
    assert "profiles" in data
    assert len(data["profiles"]) == 1
    assert data["profiles"][0]["content"] == "Fact 1"
    assert data["profiles"][0]["id"] == str(test_id)
    mock_memo_service.get_user_profiles.assert_called_once_with(DEFAULT_USER_ID, DEFAULT_SPACE_ID)

def test_create_profile_success(client: TestClient, mock_memo_service):
    """Test creating a new profile entry successfully."""
    test_id = uuid.uuid4()
    mock_memo_service.add_user_profiles.return_value = IdsData(ids=[test_id])
    
    payload = {
        "content": "New Fact",
        "attributes": {"topic": "T1", "sub_topic": "S1"}
    }
    response = client.post("/api/memory/profiles", json=payload)
    
    assert response.status_code == 200
    assert response.json()["ids"] == [str(test_id)]
    mock_memo_service.add_user_profiles.assert_called_once()
    
    # Verify exact arguments passed to the service
    _, kwargs = mock_memo_service.add_user_profiles.call_args
    assert kwargs["user_id"] == DEFAULT_USER_ID
    assert kwargs["space_id"] == DEFAULT_SPACE_ID
    assert kwargs["contents"] == ["New Fact"]
    assert kwargs["attributes"] == [{"topic": "T1", "sub_topic": "S1"}]

def test_update_profile_success(client: TestClient, mock_memo_service):
    """Test updating an existing profile entry successfully."""
    test_id = uuid.uuid4()
    mock_memo_service.update_user_profiles.return_value = IdsData(ids=[test_id])
    
    payload = {
        "content": "Updated Fact",
        "attributes": {"topic": "T2", "sub_topic": "S2"}
    }
    response = client.put(f"/api/memory/profiles/{test_id}", json=payload)
    
    assert response.status_code == 200
    mock_memo_service.update_user_profiles.assert_called_once()
    
    _, kwargs = mock_memo_service.update_user_profiles.call_args
    assert kwargs["profile_ids"] == [str(test_id)]
    assert kwargs["contents"] == ["Updated Fact"]
    assert kwargs["attributes"] == [{"topic": "T2", "sub_topic": "S2"}]

def test_delete_single_profile_success(client: TestClient, mock_memo_service):
    """Test deleting a single profile entry."""
    test_id = uuid.uuid4()
    mock_memo_service.delete_user_profiles.return_value = IdsData(ids=[test_id])
    
    response = client.delete(f"/api/memory/profiles/{test_id}")
    
    assert response.status_code == 200
    mock_memo_service.delete_user_profiles.assert_called_once_with(
        user_id=DEFAULT_USER_ID,
        space_id=DEFAULT_SPACE_ID,
        profile_ids=[str(test_id)]
    )

def test_delete_multiple_profiles_success(client: TestClient, mock_memo_service):
    """Test batch deleting profile entries via DELETE body."""
    test_ids = [uuid.uuid4(), uuid.uuid4()]
    mock_memo_service.delete_user_profiles.return_value = IdsData(ids=test_ids)
    
    str_ids = [str(tid) for tid in test_ids]
    response = client.request("DELETE", "/api/memory/profiles", json={"profile_ids": str_ids})
    
    assert response.status_code == 200
    mock_memo_service.delete_user_profiles.assert_called_once_with(
        user_id=DEFAULT_USER_ID,
        space_id=DEFAULT_SPACE_ID,
        profile_ids=str_ids
    )

def test_auto_initialization_on_first_call(client: TestClient, mock_memo_service):
    """Test that ensure_defaults (ensure_user) is called before processing requests."""
    mock_memo_service.get_profile_config.return_value = ProfileConfigData(profile_config="...")
    
    # First call - should trigger ensure_user
    client.get("/api/memory/config")
    assert mock_memo_service.ensure_user.call_count == 1
    
    # Second call in SAME test - should NOT trigger ensure_user again due to internal flag
    client.get("/api/memory/config")
    assert mock_memo_service.ensure_user.call_count == 1
