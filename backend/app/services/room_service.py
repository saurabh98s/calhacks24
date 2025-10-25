"""
Room Service - Handles room operations
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID
import uuid

from app.models.room import Room
from app.schemas.room_schema import RoomCreate, RoomUpdate


class RoomService:
    """Room management service"""
    
    @staticmethod
    async def create_room(db: AsyncSession, room_data: RoomCreate) -> Room:
        """Create a new room"""
        room = Room(
            id=uuid.uuid4(),
            room_id=room_data.room_id or f"room_{uuid.uuid4().hex[:8]}",
            name=room_data.name,
            room_type=room_data.room_type,
            ai_persona=room_data.ai_persona,
            description=room_data.description,
            max_users=room_data.max_users,
            is_public=room_data.is_public
        )
        
        db.add(room)
        await db.commit()
        await db.refresh(room)
        
        return room
    
    @staticmethod
    async def get_room_by_id(db: AsyncSession, room_id: UUID) -> Optional[Room]:
        """Get room by ID"""
        result = await db.execute(select(Room).where(Room.id == room_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_room_by_room_id(db: AsyncSession, room_id: str) -> Optional[Room]:
        """Get room by room_id string"""
        result = await db.execute(select(Room).where(Room.room_id == room_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_rooms(db: AsyncSession, public_only: bool = True) -> List[Room]:
        """Get all rooms"""
        query = select(Room)
        
        if public_only:
            query = query.where(Room.is_public == True)
        
        result = await db.execute(query)
        return list(result.scalars().all())
    
    @staticmethod
    async def get_rooms_by_type(db: AsyncSession, room_type: str) -> List[Room]:
        """Get rooms by type"""
        result = await db.execute(
            select(Room).where(Room.room_type == room_type, Room.is_public == True)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def update_room(db: AsyncSession, room_id: UUID, room_data: RoomUpdate) -> Optional[Room]:
        """Update room information"""
        room = await RoomService.get_room_by_id(db, room_id)
        
        if not room:
            return None
        
        # Update fields
        update_data = room_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)
        
        await db.commit()
        await db.refresh(room)
        
        return room
    
    @staticmethod
    async def increment_message_count(db: AsyncSession, room_id: UUID):
        """Increment room's message count"""
        room = await RoomService.get_room_by_id(db, room_id)
        if room:
            room.total_messages += 1
            await db.commit()
    
    @staticmethod
    async def update_active_users(db: AsyncSession, room_id: UUID, count: int):
        """Update active users count"""
        room = await RoomService.get_room_by_id(db, room_id)
        if room:
            room.active_users_count = count
            await db.commit()
    
    @staticmethod
    async def delete_room(db: AsyncSession, room_id: UUID):
        """Delete a room when all users have left"""
        room = await RoomService.get_room_by_id(db, room_id)
        if room:
            await db.delete(room)
            await db.commit()


room_service = RoomService()

