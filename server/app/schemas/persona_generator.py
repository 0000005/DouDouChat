from typing import Optional
from pydantic import BaseModel

class PersonaGenerateRequest(BaseModel):
    description: str
    name: Optional[str] = None

class PersonaGenerateResponse(BaseModel):
    name: str
    description: str
    system_prompt: str
    initial_message: str
