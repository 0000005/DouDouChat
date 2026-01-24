import pytest
from app.models.group import Group, GroupMember, GroupMessage
from app.services.memo.constants import DEFAULT_USER_ID

@pytest.mark.asyncio
async def test_group_chat_basic_flow(db):
    """
    Test basic group chat flow: create group, add members, send messages.
    """
    # 1. Create a group
    group = Group(
        name="Test Group",
        owner_id=DEFAULT_USER_ID,
        description="A group for testing"
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    
    assert group.id is not None
    assert group.name == "Test Group"
    
    # 2. Add members
    member1 = GroupMember(
        group_id=group.id,
        member_id=DEFAULT_USER_ID,
        member_type="user"
    )
    member2 = GroupMember(
        group_id=group.id,
        member_id="1", # Simulate a friend ID
        member_type="friend"
    )
    db.add_all([member1, member2])
    db.commit()
    
    # Verify relationships
    db.refresh(group)
    assert len(group.members) == 2
    assert any(m.member_type == "user" for m in group.members)
    assert any(m.member_type == "friend" for m in group.members)
    
    # 3. Send messages
    msg1 = GroupMessage(
        group_id=group.id,
        sender_id=DEFAULT_USER_ID,
        sender_type="user",
        content="Hello everyone!"
    )
    msg2 = GroupMessage(
        group_id=group.id,
        sender_id="1",
        sender_type="friend",
        content="Hi there!",
        mentions=[DEFAULT_USER_ID]
    )
    db.add_all([msg1, msg2])
    db.commit()
    
    # Verify messages
    db.refresh(group)
    assert len(group.messages) == 2
    assert group.messages[0].content == "Hello everyone!"
    assert group.messages[1].mentions == [DEFAULT_USER_ID]
    assert group.messages[1].sender_type == "friend"

@pytest.mark.asyncio
async def test_group_cascade_delete(db):
    """
    Test that deleting a group also deletes its members and messages.
    """
    group = Group(name="Delete Me", owner_id=DEFAULT_USER_ID)
    db.add(group)
    db.commit()
    db.refresh(group)
    
    member = GroupMember(group_id=group.id, member_id=DEFAULT_USER_ID, member_type="user")
    message = GroupMessage(group_id=group.id, sender_id=DEFAULT_USER_ID, sender_type="user", content="Bye")
    db.add_all([member, message])
    db.commit()
    
    group_id = group.id
    db.delete(group)
    db.commit()
    
    # Check if members and messages are gone
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    messages = db.query(GroupMessage).filter(GroupMessage.group_id == group_id).all()
    
    assert len(members) == 0
    assert len(messages) == 0
