"""
Initialize default rooms on startup
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.room import Room
from app.services.context_manager import context_manager

logger = logging.getLogger(__name__)


async def initialize_default_rooms(db: AsyncSession):
    """Create default rooms if they don't exist"""
    
    default_rooms = [
        {
            "room_id": "dnd_campaign_hall",
            "name": "🎲 Dungeons & Dragons - The Dragon's Keep",
            "room_type": "dnd",
            "ai_persona": "Dungeon Master Thaldrin",
            "description": "Epic D&D adventures await! Roll for initiative and embark on quests.",
            "is_public": True,
        },
        {
            "room_id": "aa_support_circle",
            "name": "🤝 Alcoholics Anonymous - Safe Haven",
            "room_type": "alcoholics_anonymous",
            "ai_persona": "Sponsor Morgan",
            "description": "Confidential support group for recovery. Share your journey in a judgment-free space.",
            "is_public": True,
        },
        {
            "room_id": "group_therapy_space",
            "name": "💚 Group Therapy - Healing Together",
            "room_type": "group_therapy",
            "ai_persona": "Dr. Sarah Chen",
            "description": "Professional group therapy for mental health support and healing.",
            "is_public": True,
        },
        {
            "room_id": "private_room_default",
            "name": "Private Room",
            "room_type": "dnd",
            "ai_persona": "Atlas",
            "description": "Your personal chat space",
            "is_public": True,
        }
    ]
    
    created_count = 0
    
    for room_data in default_rooms:
        try:
            # Check if room already exists
            result = await db.execute(
                select(Room).where(Room.room_id == room_data["room_id"])
            )
            existing_room = result.scalar_one_or_none()
            
            if not existing_room:
                # Create new room
                room = Room(**room_data)
                db.add(room)
                await db.flush()
                
                # Initialize room state in Redis
                await context_manager.initialize_room_state(
                    room.room_id,
                    room.room_type,
                    room.ai_persona
                )
                
                created_count += 1
                logger.info(f"✅ Created room: {room_data['name']} ({room_data['room_id']})")
            else:
                logger.info(f"ℹ️  Room already exists: {room_data['room_id']}")
        
        except Exception as e:
            logger.error(f"❌ Failed to create room {room_data['room_id']}: {e}")
    
    if created_count > 0:
        await db.commit()
        logger.info(f"🎉 Initialized {created_count} default rooms")
    else:
        logger.info("ℹ️  All default rooms already exist")
    
    return created_count

