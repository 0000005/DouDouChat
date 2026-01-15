from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, UniqueConstraint
from app.db.base import Base
from app.db.types import UTCDateTime, utc_now


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)  # int, bool, string, float, json
    description = Column(Text, nullable=True)
    created_at = Column(UTCDateTime, default=utc_now, nullable=False)
    updated_at = Column(UTCDateTime, default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("group_name", "key", name="uq_system_settings_group_key"),
    )

