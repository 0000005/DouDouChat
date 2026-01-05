from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class SystemSettingBase(BaseModel):
    group_name: str
    key: str
    value: Any
    value_type: str
    description: Optional[str] = None

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None

class SystemSetting(SystemSettingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemSettingUpdateBulk(BaseModel):
    settings: dict = Field(..., description="Key-value pairs of settings within a group")
