from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class MessageBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(MessageBase):
    room_id: UUID


class MessageResponse(MessageBase):
    id: UUID
    room_id: UUID
    user_id: Optional[UUID] = None
    message_type: str
    ai_persona: Optional[str] = None
    ai_trigger: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class MessageSocketData(BaseModel):
    """Schema for WebSocket message events"""
    message_id: str
    room_id: str
    user_id: Optional[str] = None
    username: str
    content: str
    message_type: str = "user"
    ai_persona: Optional[str] = None
    timestamp: datetime
    avatar_style: Optional[str] = None
    avatar_color: Optional[str] = None

