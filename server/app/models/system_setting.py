from sqlalchemy import Column, Integer, String, Text, DateTime, func, UniqueConstraint
from app.db.base import Base

class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    value = Column(Text, nullable=False)
    value_type = Column(String(20), nullable=False)  # int, bool, string, float, json
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("group_name", "key", name="uq_system_settings_group_key"),
    )
