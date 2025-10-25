"""
User Service - Handles user operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID
import uuid

from app.models.user import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import get_password_hash


class UserService:
    """User management service"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        user = User(
            id=uuid.uuid4(),
            username=user_data.username,
            email=user_data.email,
            avatar_style=user_data.avatar_style,
            avatar_color=user_data.avatar_color,
            mood_icon=user_data.mood_icon,
            bio=user_data.bio,
            is_guest=user_data.is_guest,
            current_room_id=user_data.room_id  # Assign to room
        )
        
        # Hash password if provided
        if user_data.password and not user_data.is_guest:
            user.hashed_password = get_password_hash(user_data.password)
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username (first match - may not be unique)"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_username_and_room(
        db: AsyncSession, username: str, room_id: str
    ) -> Optional[User]:
        """Get user by username in specific room"""
        result = await db.execute(
            select(User).where(
                User.username == username,
                User.current_room_id == room_id
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_users_in_room(db: AsyncSession, room_id: str) -> list[User]:
        """Get all users in a specific room"""
        result = await db.execute(
            select(User).where(User.current_room_id == room_id)
        )
        return result.scalars().all()
    
    @staticmethod
    async def remove_user_from_room(db: AsyncSession, user_id: UUID):
        """Remove user from their current room (set to NULL)"""
        user = await UserService.get_user_by_id(db, user_id)
        if user:
            user.current_room_id = None
            await db.commit()
    
    @staticmethod
    async def delete_guest_user(db: AsyncSession, user_id: UUID):
        """Delete a guest user (for cleanup when they leave)"""
        user = await UserService.get_user_by_id(db, user_id)
        if user and user.is_guest:
            await db.delete(user)
            await db.commit()
    
    @staticmethod
    async def update_user(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await UserService.get_user_by_id(db, user_id)
        
        if not user:
            return None
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await db.commit()
        await db.refresh(user)
        
        return user
    
    @staticmethod
    async def increment_message_count(db: AsyncSession, user_id: UUID):
        """Increment user's message count"""
        user = await UserService.get_user_by_id(db, user_id)
        if user:
            user.total_messages += 1
            await db.commit()
    
    @staticmethod
    async def update_engagement_score(db: AsyncSession, user_id: UUID, score_delta: int):
        """Update user's engagement score"""
        user = await UserService.get_user_by_id(db, user_id)
        if user:
            user.engagement_score += score_delta
            await db.commit()


user_service = UserService()

