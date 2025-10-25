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
            "room_id": "tutorial_hallway",
            "name": "Tutorial Hallway",
            "room_type": "tutorial",
            "ai_persona": "atlas",
            "description": "Learn how to use ChatRealm",
            "is_public": True,
        },
        {
            "room_id": "study_group_bio101",
            "name": "Study Group - Biology 101",
            "room_type": "study_group",
            "ai_persona": "dr_chen",
            "description": "Collaborative learning space for biology students",
            "is_public": True,
        },
        {
            "room_id": "support_circle_main",
            "name": "Support Circle",
            "room_type": "support_circle",
            "ai_persona": "sam",
            "description": "Safe space for sharing and support",
            "is_public": True,
        },
        {
            "room_id": "casual_lounge",
            "name": "Casual Lounge",
            "room_type": "casual_lounge",
            "ai_persona": "rex",
            "description": "Hang out and chat casually",
            "is_public": True,
        },
        {
            "room_id": "private_room_default",
            "name": "Private Room",
            "room_type": "private",
            "ai_persona": "atlas",
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

