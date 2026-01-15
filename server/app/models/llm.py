from sqlalchemy import Column, Integer, String, Boolean
from datetime import datetime, timezone
from app.db.base import Base
from app.db.types import UTCDateTime, utc_now


class LLMConfig(Base):
    __tablename__ = "llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    base_url = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    model_name = Column(String, default="gpt-3.5-turbo")
    create_time = Column(UTCDateTime, default=utc_now)
    update_time = Column(UTCDateTime, default=utc_now, onupdate=utc_now)
    deleted = Column(Boolean, default=False)

