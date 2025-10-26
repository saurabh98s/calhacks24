"""
Room routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.room_schema import RoomCreate, RoomResponse, RoomListResponse, RoomUpdate
from app.services.room_service import room_service
from app.services.context_manager import context_manager

router = APIRouter()


@router.get("/", response_model=List[RoomListResponse])
async def get_rooms(
    room_type: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all public rooms"""
    
    if room_type:
        rooms = await room_service.get_rooms_by_type(db, room_type)
    else:
        rooms = await room_service.get_all_rooms(db, public_only=True)
    
    return rooms


@router.post("/", response_model=RoomResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: RoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new room"""
    
    # Create room in database
    room = await room_service.create_room(db, room_data)
    
    # Initialize room state in Redis
    await context_manager.initialize_room_state(
        room.room_id,
        room.room_type,
        room.ai_persona
    )
    
    return room


@router.get("/{room_id}", response_model=RoomResponse)
async def get_room(
    room_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get room by ID"""
    
    room = await room_service.get_room_by_room_id(db, room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    return room


@router.patch("/{room_id}", response_model=RoomResponse)
async def update_room(
    room_id: str,
    room_data: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update room"""
    
    room = await room_service.get_room_by_room_id(db, room_id)
    
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    updated_room = await room_service.update_room(db, room.id, room_data)
    
    return updated_room


# Predefined rooms initialization
@router.post("/initialize-defaults", status_code=status.HTTP_201_CREATED)
async def initialize_default_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Initialize default rooms for the platform"""
    
    default_rooms = [
        {
            "room_id": "dnd_campaign_hall",
            "name": "🎲 Dungeons & Dragons - The Dragon's Keep",
            "room_type": "dnd",
            "ai_persona": "Dungeon Master Thaldrin",
            "description": "Epic D&D adventures await! Roll for initiative and embark on quests."
        },
        {
            "room_id": "aa_support_circle",
            "name": "🤝 Alcoholics Anonymous - Safe Haven",
            "room_type": "alcoholics_anonymous",
            "ai_persona": "Sponsor Morgan",
            "description": "Confidential support group for recovery. Share your journey in a judgment-free space."
        },
        {
            "room_id": "group_therapy_space",
            "name": "💚 Group Therapy - Healing Together",
            "room_type": "group_therapy",
            "ai_persona": "Dr. Sarah Chen",
            "description": "Professional group therapy for mental health support and healing."
        }
    ]
    
    created_rooms = []
    
    for room_data in default_rooms:
        # Check if exists
        existing = await room_service.get_room_by_room_id(db, room_data["room_id"])
        
        if not existing:
            room_create = RoomCreate(**room_data)
            room = await room_service.create_room(db, room_create)
            
            # Initialize state
            await context_manager.initialize_room_state(
                room.room_id,
                room.room_type,
                room.ai_persona
            )
            
            created_rooms.append(room)
    
    return {"created": len(created_rooms), "rooms": created_rooms}

