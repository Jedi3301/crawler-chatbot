from pydantic import BaseModel, Field
from datetime import datetime

class BotCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None

class BotResponse(BaseModel):
    id: str
    name: str
    description: str | None
    created_at: datetime
