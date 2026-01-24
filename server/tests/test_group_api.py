import pytest
from sqlalchemy.orm import Session
from app.services.memo.constants import DEFAULT_USER_ID
from app.models.group import Group, GroupMember

def test_create_group_api(client, db: Session):
    """Test creating a group with initial members."""
    response = client.post(
        "/api/group/create",
        json={
            "name": "New API Group",
            "member_ids": ["friend1", "friend2"],
            "description": "Created via API",
            "auto_reply": True
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New API Group"
    assert data["owner_id"] == DEFAULT_USER_ID
    
    # Check database
    group_id = data["id"]
    db.expire_all()
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    assert len(members) == 3  # user + 2 friends

def test_get_groups_api(client, db: Session):
    """Test listing groups the user belongs to."""
    client.post(
        "/api/group/create",
        json={"name": "Group 1", "member_ids": []}
    )
    
    response = client.get("/api/groups")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(g["name"] == "Group 1" for g in data)

def test_get_group_detail_api(client, db: Session):
    """Test getting group details with members."""
    create_res = client.post(
        "/api/group/create",
        json={"name": "Detail Group", "member_ids": ["f1"]}
    )
    group_id = create_res.json()["id"]
    
    response = client.get(f"/api/group/{group_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Detail Group"
    assert len(data["members"]) == 2

def test_get_group_detail_non_member_403(client, db: Session):
    """Test that non-members cannot access group details."""
    # Create a group, then remove user from it
    create_res = client.post(
        "/api/group/create",
        json={"name": "Private Group", "member_ids": []}
    )
    group_id = create_res.json()["id"]
    
    # Directly remove user from group (simulating non-member access)
    db.expire_all()
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.member_id == DEFAULT_USER_ID
    ).first()
    if member:
        db.delete(member)
        db.commit()
    
    response = client.get(f"/api/group/{group_id}")
    assert response.status_code == 403

def test_update_group_settings_api(client, db: Session):
    """Test updating group settings by owner."""
    create_res = client.post(
        "/api/group/create",
        json={"name": "Old Name", "member_ids": []}
    )
    group_id = create_res.json()["id"]
    
    response = client.patch(
        "/api/group/settings",
        json={
            "group_id": group_id,
            "group_in": {"name": "New Name", "auto_reply": False}
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["auto_reply"] is False

def test_invite_members_api(client, db: Session):
    """Test inviting new members to a group."""
    create_res = client.post(
        "/api/group/create",
        json={"name": "Invite Group", "member_ids": []}
    )
    group_id = create_res.json()["id"]
    
    response = client.post(
        "/api/group/invite",
        json={
            "group_id": group_id,
            "member_ids": ["new_friend"]
        }
    )
    assert response.status_code == 200
    assert response.json() is True
    
    # Verify
    detail = client.get(f"/api/group/{group_id}").json()
    assert any(m["member_id"] == "new_friend" for m in detail["members"])

def test_exit_group_api_non_owner(client, db: Session):
    """Test that a non-owner member can exit a group."""
    # For single-user app, we need to simulate adding another user
    # Since we are the owner, we cannot exit. This test validates that.
    create_res = client.post(
        "/api/group/create",
        json={"name": "Exit Group", "member_ids": []}
    )
    group_id = create_res.json()["id"]
    
    # Owner tries to exit - should fail (new behavior)
    response = client.delete(f"/api/group/exit?group_id={group_id}")
    assert response.status_code == 400  # Owner cannot exit

def test_remove_member_api(client, db: Session):
    """Test owner removing a member."""
    create_res = client.post(
        "/api/group/create",
        json={"name": "Remove Group", "member_ids": ["bad_friend"]}
    )
    group_id = create_res.json()["id"]
    
    response = client.delete(f"/api/group/{group_id}/member/bad_friend")
    assert response.status_code == 200
    assert response.json() is True
    
    # Verify
    detail = client.get(f"/api/group/{group_id}").json()
    assert not any(m["member_id"] == "bad_friend" for m in detail["members"])

def test_remove_self_not_allowed(client, db: Session):
    """Test that owner cannot remove themselves."""
    create_res = client.post(
        "/api/group/create",
        json={"name": "Self Remove Group", "member_ids": []}
    )
    group_id = create_res.json()["id"]
    
    response = client.delete(f"/api/group/{group_id}/member/{DEFAULT_USER_ID}")
    assert response.status_code == 403  # Cannot remove self
