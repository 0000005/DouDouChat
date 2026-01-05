from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.settings_service import SettingsService, NOT_FOUND
from app.schemas.system_setting import SystemSetting, SystemSettingUpdateBulk

router = APIRouter()

class SettingValueUpdate(BaseModel):
    """单个设置值更新的 Request Body"""
    value: Any

@router.get("/{group_name}", response_model=Dict[str, Any])
def get_settings_by_group(group_name: str, db: Session = Depends(get_db)):
    """获取指定分组的所有设置"""
    return SettingsService.get_settings_by_group(db, group_name)

@router.post("/{group_name}/bulk")
def update_settings_bulk(
    group_name: str, 
    payload: SystemSettingUpdateBulk, 
    db: Session = Depends(get_db)
):
    """批量更新指定分组的设置"""
    for key, value in payload.settings.items():
        SettingsService.set_setting(db, group_name, key, value)
    return {"status": "success"}

@router.get("/{group_name}/{key}", response_model=Any)
def get_setting(group_name: str, key: str, db: Session = Depends(get_db)):
    """获取单个设置值"""
    val = SettingsService.get_setting(db, group_name, key, NOT_FOUND)
    if val is NOT_FOUND:
        raise HTTPException(status_code=404, detail="Setting not found")
    return val

@router.put("/{group_name}/{key}")
def update_setting(
    group_name: str, 
    key: str, 
    body: SettingValueUpdate,
    db: Session = Depends(get_db)
):
    """更新单个设置"""
    SettingsService.set_setting(db, group_name, key, body.value)
    return {"status": "success"}
