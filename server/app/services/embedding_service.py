from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.embedding import EmbeddingSetting
from app.schemas.embedding import EmbeddingSettingCreate, EmbeddingSettingUpdate

class EmbeddingService:
    @staticmethod
    def get_setting(db: Session, setting_id: int) -> Optional[EmbeddingSetting]:
        return db.query(EmbeddingSetting).filter(EmbeddingSetting.id == setting_id, EmbeddingSetting.deleted == False).first()

    @staticmethod
    def get_multi(db: Session, skip: int = 0, limit: int = 100) -> List[EmbeddingSetting]:
        return db.query(EmbeddingSetting).filter(EmbeddingSetting.deleted == False).offset(skip).limit(limit).all()

    @staticmethod
    def create_setting(db: Session, obj_in: EmbeddingSettingCreate) -> EmbeddingSetting:
        db_obj = EmbeddingSetting(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def update_setting(db: Session, db_obj: EmbeddingSetting, obj_in: EmbeddingSettingUpdate) -> EmbeddingSetting:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete_setting(db: Session, db_obj: EmbeddingSetting) -> EmbeddingSetting:
        # Soft delete
        db_obj.deleted = True
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

embedding_service = EmbeddingService()
