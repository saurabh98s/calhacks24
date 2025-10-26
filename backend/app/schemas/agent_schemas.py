"""
Pydantic Models for Agentverse Multi-Agent Communication
"""
from uagents import Model
from typing import List


# ============================================================================
# RESPONSE COORDINATOR MODELS
# ============================================================================

class ResponseRequest(Model):
    """Request to determine if AI should respond"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    recent_messages: List[str] = []
    room_type: str = "chat"
    context: str = "{}"


class ResponseDecision(Model):
    """AI response decision"""
    should_respond: bool
    response_type: str  # "answer", "clarify", "support", "moderate", "none"
    suggested_response: str
    confidence: float
    reasoning: str
    urgency: str  # "immediate", "normal", "low", "none"
    tone: str  # "helpful", "empathetic", "professional", "casual", "firm"


class ResponseCoordinatorResponse(Model):
    """Response with decision"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    decision: ResponseDecision
    processing_time: float


# ============================================================================
# CONTEXT MANAGER MODELS
# ============================================================================

class ContextRequest(Model):
    """Request to manage context"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    room_type: str = "chat"
    context: str = "{}"


class UserContextData(Model):
    """User context information"""
    participation_level: int
    message_count: int
    first_message: str
    last_active: str
    topics_engaged: List[str]
    questions_asked: int


class RoomContextData(Model):
    """Room context information"""
    total_messages: int
    active_users: int
    current_topic: str
    recent_topics: List[str]
    activity_level: str


class ParticipationMetrics(Model):
    """Participation metrics"""
    participation_rate: float
    rank: str
    is_new_user: bool


class ContextResponse(Model):
    """Response with context data"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    user_context: UserContextData
    room_context: RoomContextData
    participation_metrics: ParticipationMetrics
    processing_time: float


# ============================================================================
# WELLNESS GUARDIAN MODELS
# ============================================================================

class WellnessRequest(Model):
    """Request to monitor wellness"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    room_type: str = "chat"
    context: str = "{}"


class WellnessAnalysis(Model):
    """Wellness analysis result"""
    crisis: bool
    needs_support: bool
    indicators: List[str]
    severity: str
    wellness_score: float
    crisis_pattern: bool
    response: str
    action_required: str
    confidence: float


class WellnessResponse(Model):
    """Response with wellness analysis"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    analysis: WellnessAnalysis
    processing_time: float


# ============================================================================
# EMOTION TRACKER MODELS
# ============================================================================

class EmotionRequest(Model):
    """Request to analyze message emotion"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    room_type: str = "chat"
    context: str = "{}"


class EmotionAnalysis(Model):
    """Emotion analysis result"""
    emotion: str
    score: float
    intensity: int
    trend: str
    alerts: List[str]
    confidence: float


class EmotionResponse(Model):
    """Response with emotion analysis"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    analysis: EmotionAnalysis
    processing_time: float


# ============================================================================
# TOXICITY DETECTOR MODELS
# ============================================================================

class ToxicityRequest(Model):
    """Request to analyze message toxicity"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    message_content: str
    room_type: str = "chat"
    context: str = "{}"


class ToxicityAnalysis(Model):
    """Toxicity analysis result"""
    toxicity_score: int
    severity: str
    action: str
    categories: List[str]
    reasoning: str
    requires_wellness_check: bool
    confidence: float
    model: str


class ToxicityResponse(Model):
    """Response with analysis"""
    query_id: str
    message_id: str
    user_id: str
    room_id: str
    analysis: ToxicityAnalysis
    processing_time: float

