from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from datetime import datetime, timezone
from app.db.base import Base
from app.db.types import UTCDateTime, utc_now


class FriendTemplate(Base):
    __tablename__ = "friend_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False)
    avatar = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=False)
    initial_message = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, default=utc_now, nullable=False)
    updated_at = Column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)
