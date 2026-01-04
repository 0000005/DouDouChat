from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.db.base import Base

class EmbeddingSetting(Base):
    __tablename__ = "embedding_settings"

    id = Column(Integer, primary_key=True, index=True)
    # 提供商："openai" (默认)、"jina"、"lmstudio"、"ollama"
    embedding_provider = Column(String, default="openai")
    # 密钥
    embedding_api_key = Column(String, nullable=True)
    # 地址
    embedding_base_url = Column(String, nullable=True)
    # 向量维度
    embedding_dim = Column(Integer, default=1024)
    # 模型名称
    embedding_model = Column(String, default="BAAI/bge-m3")
    # 最大token数
    embedding_max_token_size = Column(Integer, default=8000)

    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted = Column(Boolean, default=False)
