"""
Trigger detection system for AI responses
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class TriggerDetector:
    """Detects when AI should intervene in conversations"""
    
    @staticmethod
    def detect_trigger(
        message: str,
        user_state: Dict[str, Any],
        room_state: Dict[str, Any],
        ai_persona: str
    ) -> Optional[Dict[str, Any]]:
        """
        INTELLIGENT: Analyze message and multi-user context to determine AI response strategy
        
        Key principles:
        - 1 user alone: AI is conversational companion (respond frequently)
        - 2+ users: AI facilitates but lets users talk to each other
        - Always detect @mentions and direct questions
        - Never interrupt user-to-user conversations
        """
        message_lower = message.lower()
        ai_name = ai_persona.lower()
        user_id = user_state.get("user_id")
        
        # Count ACTUAL active users (check participation, not just presence)
        participation = user_state.get("participation", {})
        message_count = participation.get("message_count", 0)
        
        # Detect user engagement signals
        engagement_phrases = [
            "don't know", "dont know", "idk", "not sure", "help me",
            "bored", "lonely", "anyone there", "hello?", "hey?",
            "what should", "any ideas", "suggestions"
        ]
        
        disengagement_phrases = [
            "don't know what", "nothing to say", "idk what", 
            "not sure what", "what to talk about", "what to say"
        ]
        
        # 0. CRITICAL: Single user alone - AI should be VERY engaged!
        # This is a 1-on-1 conversation, AI should respond to almost everything
        if message_count <= 3 or any(phrase in message_lower for phrase in disengagement_phrases):
            # New user OR user expressing disengagement
            return {
                "type": "single_user_engagement",
                "priority": "high",
                "target_user": user_id,
                "context": "User needs engagement - provide interesting conversation starter or response"
            }
        
        # 1. Direct mention of AI - ALWAYS RESPOND!
        if f"@{ai_name}" in message_lower or f"@atlas" in message_lower:
            return {
                "type": "direct_mention",
                "priority": "critical",
                "target_user": user_id,
                "context": "User directly mentioned AI - respond immediately!"
            }
        
        # 2. User-to-user conversation detection
        # If user mentions another user (not AI), stay quiet
        if "@" in message and ai_name not in message_lower:
            # User talking to another user - AI should NOT interrupt
            return None
        
        # 3. Question asked - AI should help!
        if "?" in message:
            # Check if it's directed at another user
            if "@" in message and ai_name not in message_lower:
                return None  # Let users talk
            
            return {
                "type": "question_asked",
                "priority": "high",
                "target_user": user_id,
                "context": "User asked a question - provide helpful answer"
            }
        
        # 4. Confusion or need for help
        confusion_phrases = [
            "confused", "don't understand", "dont understand",
            "lost", "unclear", "help", "stuck", "can't figure"
        ]
        if any(phrase in message_lower for phrase in confusion_phrases):
            return {
                "type": "user_confusion",
                "priority": "high",
                "target_user": user_id,
                "context": "User needs help or clarification"
            }
        
        # 5. User seeking engagement
        if any(phrase in message_lower for phrase in engagement_phrases):
            return {
                "type": "engagement_request",
                "priority": "medium",
                "target_user": user_id,
                "context": "User is seeking conversation or ideas"
            }
        
        # 6. Question words (implicit questions)
        question_words = ["how do", "what is", "why is", "who is", "when is", "where is"]
        if any(word in message_lower for word in question_words):
            return {
                "type": "question_asked",
                "priority": "high",
                "target_user": user_id,
                "context": "User asked implicit question"
            }
        
        # 7. For multi-user rooms: Only respond if truly needed
        # Don't interrupt active conversations between users
        # Let the silence monitoring handle this
        return None
    
    @staticmethod
    def check_silence_threshold(user_state: Dict[str, Any], threshold: int = 120) -> Optional[Dict[str, Any]]:
        """Check if user has been silent too long"""
        silence_duration = user_state.get("participation", {}).get("silence_duration", 0)
        
        if silence_duration >= threshold:
            return {
                "type": "silence_threshold",
                "priority": "medium",
                "target_user": user_state.get("user_id"),
                "context": f"User silent for {silence_duration} seconds"
            }
        
        return None
    
    @staticmethod
    def check_group_silence(room_state: Dict[str, Any], threshold: int = 45) -> Optional[Dict[str, Any]]:
        """Check if entire group has been silent"""
        # This would check last message timestamp in room
        # Simplified for now
        return None
    
    @staticmethod
    def check_new_user(user_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if user just joined - ALWAYS trigger welcome for new users"""
        if user_state.get("is_new_to_room", False):
            username = user_state.get("name", "User")
            return {
                "type": "new_user_joined",
                "priority": "high",
                "target_user": user_state.get("user_id"),
                "context": f"{username} just entered the room and needs to be welcomed and looped into the conversation"
            }
        
        return None
    
    @staticmethod
    def check_conflict(room_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check for conflict or tension in room"""
        if room_state.get("dynamics", {}).get("conflict_detected", False):
            return {
                "type": "conflict_detected",
                "priority": "high",
                "context": "Tension detected between users"
            }
        
        return None

