import asyncio
from app.core.config import settings
from app.vendor.memobase_server.connectors import init_db
from app.vendor.memobase_server.env import reinitialize_config
from app.vendor.memobase_server.controllers.buffer_background import start_memobase_worker

async def initialize_memo_sdk():
    """
    Initialize the Memobase SDK with settings from the main app.
    """
    # 1. Map main app settings to Memobase config
    # The keys in settings already follow MEMOBASE_* prefix or we can map them explicitly
    memo_config = {
        "llm_api_key": settings.MEMOBASE_LLM_API_KEY,
        "llm_base_url": settings.MEMOBASE_LLM_BASE_URL,
        "best_llm_model": settings.MEMOBASE_BEST_LLM_MODEL,
        "enable_event_embedding": settings.MEMOBASE_ENABLE_EVENT_EMBEDDING,
        "embedding_api_key": settings.MEMOBASE_EMBEDDING_API_KEY,
        "embedding_base_url": settings.MEMOBASE_EMBEDDING_BASE_URL,
        "embedding_model": settings.MEMOBASE_EMBEDDING_MODEL,
        "embedding_dim": settings.MEMOBASE_EMBEDDING_DIM,
    }
    
    # 2. Reinitialize the global CONFIG object in SDK
    reinitialize_config(memo_config)
    
    # 3. Initialize Database
    init_db(settings.MEMOBASE_DB_URL)
    
    # 4. Start background worker
    worker_task = asyncio.create_task(start_memobase_worker(interval_s=60))
    
    return worker_task
