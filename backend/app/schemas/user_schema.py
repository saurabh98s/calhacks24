from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    avatar_style: str = "human"
    avatar_color: str = "blue"
    mood_icon: str = "😊"
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: Optional[str] = None
    is_guest: bool = False


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    avatar_style: Optional[str] = None
    avatar_color: Optional[str] = None
    mood_icon: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    engagement_score: int
    total_messages: int
    rooms_joined: int
    is_active: bool
    is_guest: bool
    created_at: datetime
    last_seen: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None

