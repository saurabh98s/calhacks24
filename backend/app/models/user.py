from sqlalchemy import Column, String, DateTime, Boolean, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), nullable=False)  # Removed unique=True
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)
    current_room_id = Column(String(100), nullable=True)  # Track current room
    
    # Avatar info
    avatar_style = Column(String(50), default="human")
    avatar_color = Column(String(50), default="blue")
    mood_icon = Column(String(50), default="😊")
    bio = Column(String(500), nullable=True)
    
    # Stats
    engagement_score = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    rooms_joined = Column(Integer, default=0)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    is_guest = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    
    # Composite unique constraint: username must be unique per room
    __table_args__ = (
        UniqueConstraint('username', 'current_room_id', name='uix_username_room'),
        Index('ix_username_room', 'username', 'current_room_id'),
    )
    
    def __repr__(self):
        return f"<User {self.username} in room {self.current_room_id}>"

