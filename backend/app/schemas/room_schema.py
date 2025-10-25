from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    room_type: str = Field(..., pattern="^(study_group|support_circle|casual_lounge|private|tutorial)$")
    ai_persona: str
    description: Optional[str] = None
    max_users: int = 10
    is_public: bool = True


class RoomCreate(RoomBase):
    room_id: Optional[str] = None


class RoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_users: Optional[int] = None
    is_public: Optional[bool] = None


class RoomResponse(RoomBase):
    id: UUID
    room_id: str
    ai_persona_config: Optional[Dict[str, Any]] = None
    background_image: Optional[str] = None
    created_at: datetime
    active_users_count: int
    total_messages: int
    
    class Config:
        from_attributes = True


class RoomListResponse(BaseModel):
    id: UUID
    room_id: str
    name: str
    room_type: str
    description: Optional[str] = None
    active_users_count: int
    max_users: int
    ai_persona: str
    
    class Config:
        from_attributes = True

