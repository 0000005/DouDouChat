import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.api.api import api_router
from app.db.init_db import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database
    init_db()
    
    # Initialize Memobase SDK
    from app.services.memo import initialize_memo_sdk
    memo_worker_task = await initialize_memo_sdk()
    
    yield
    
    # Clean up
    if memo_worker_task:
        memo_worker_task.cancel()
        try:
            await memo_worker_task
        except asyncio.CancelledError:
            pass

app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.include_router(api_router, prefix=settings.API_STR)

@app.get("/")
def root():
    return {"message": "Welcome to DouDouChat API"}
