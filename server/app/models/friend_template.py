from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.base import Base


class FriendTemplate(Base):
    __tablename__ = "friend_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    avatar = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    initial_message = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
