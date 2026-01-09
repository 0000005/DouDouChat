from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas import friend as friend_schemas
from app.schemas import friend_template as friend_template_schemas
from app.schemas import persona_generator as persona_schemas
from app.services import friend_template_service
from app.services.persona_generator_service import persona_generator_service

router = APIRouter()


@router.get("/", response_model=List[friend_template_schemas.FriendTemplate])
def read_friend_templates(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    tag: Optional[str] = None,
    q: Optional[str] = None,
):
    return friend_template_service.get_friend_templates(
        db,
        page=page,
        size=size,
        tag=tag,
        q=q,
    )


@router.post("/{template_id}/clone", response_model=friend_schemas.Friend)
def clone_friend_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
):
    friend = friend_template_service.create_friend_from_template(db, template_id)
    if not friend:
        raise HTTPException(status_code=404, detail="Friend template not found")
    return friend


@router.post("/create-friend", response_model=friend_schemas.Friend)
def create_friend_from_template(
    *,
    db: Session = Depends(deps.get_db),
    payload: friend_template_schemas.FriendTemplateCreateFriend,
):
    return friend_template_service.create_friend_from_payload(db, payload)


@router.post("/generate", response_model=persona_schemas.PersonaGenerateResponse)
async def generate_persona(
    *,
    db: Session = Depends(deps.get_db),
    payload: persona_schemas.PersonaGenerateRequest,
):
    """
    根据描述自动生成 Persona 设定
    """
    return await persona_generator_service.generate_persona(db, payload)
