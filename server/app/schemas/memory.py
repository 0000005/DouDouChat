from typing import Optional
from pydantic import BaseModel

class ProfileAttributes(BaseModel):
    topic: str
    sub_topic: Optional[str] = None

class ProfileCreate(BaseModel):
    content: str
    attributes: ProfileAttributes

class ProfileUpdate(BaseModel):
    content: str
    attributes: Optional[ProfileAttributes] = None # 传 None 表示不分类

class ConfigUpdate(BaseModel):
    profile_config: str

class BatchDeleteRequest(BaseModel):
    profile_ids: list[str]

class StatusResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None

class CreateProfileResponse(StatusResponse):
    ids: list[str]
