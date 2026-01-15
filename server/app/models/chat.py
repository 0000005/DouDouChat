from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from app.db.types import UTCDateTime, utc_now


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    friend_id = Column(Integer, ForeignKey("friends.id"), nullable=False)
    title = Column(String(128), default="新对话", nullable=True)
    create_time = Column(UTCDateTime, default=utc_now, nullable=False)
    update_time = Column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)
    # 是否已经生成记忆
    memory_generated = Column(Boolean, default=False, nullable=False)
    # 最后一条消息的时间
    last_message_time = Column(UTCDateTime, nullable=True)

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    # friend = relationship("Friend") # Optional, if needed


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    friend_id = Column(Integer, ForeignKey("friends.id"), nullable=True)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    create_time = Column(UTCDateTime, default=utc_now, nullable=False)
    update_time = Column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)
    deleted = Column(Boolean, default=False, nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


