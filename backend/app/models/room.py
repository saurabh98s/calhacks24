from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    room_type = Column(String(50), nullable=False)  # study_group, support_circle, casual_lounge, private
    
    # AI Configuration
    ai_persona = Column(String(50), nullable=False)  # dr_chen, sam, rex, atlas
    ai_persona_config = Column(JSON, nullable=True)
    
    # Room Settings
    description = Column(Text, nullable=True)
    max_users = Column(Integer, default=10)
    is_public = Column(Boolean, default=True)
    background_image = Column(String(255), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    active_users_count = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Room {self.name} ({self.room_type})>"

