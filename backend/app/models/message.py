from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Message Content
    content = Column(Text, nullable=False)
    message_type = Column(String(50), default="user")  # user, ai, system
    
    # AI Metadata (if from AI)
    ai_persona = Column(String(50), nullable=True)
    ai_trigger = Column(String(100), nullable=True)  # direct_mention, silence_threshold, etc.
    
    # Sentiment Analysis
    sentiment = Column(String(50), nullable=True)  # positive, neutral, negative, frustrated
    sentiment_score = Column(Float, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    edited_at = Column(DateTime(timezone=True), nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Message {self.id} from {self.user_id}>"

