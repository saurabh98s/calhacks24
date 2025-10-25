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
        Analyze message and states to determine if AI should respond
        Returns trigger info or None
        """
        message_lower = message.lower()
        ai_name = ai_persona.lower()
        
        # 1. Direct mention of AI
        if f"@{ai_name}" in message_lower or ai_name in message_lower:
            return {
                "type": "direct_mention",
                "priority": "high",
                "target_user": user_state.get("user_id"),
                "context": "User directly addressed the AI"
            }
        
        # 2. User confusion detected
        confusion_phrases = ["confused", "don't understand", "lost", "unclear", "help", "what do", "how do"]
        if any(phrase in message_lower for phrase in confusion_phrases):
            return {
                "type": "user_confusion",
                "priority": "high",
                "target_user": user_state.get("user_id"),
                "context": "User expressed confusion or need for help"
            }
        
        # 3. Question asked (questions are important!)
        question_indicators = ["?", "what", "why", "how", "when", "where", "who", "can you"]
        if any(indicator in message_lower for indicator in question_indicators):
            return {
                "type": "question_asked",
                "priority": "high",  # Changed from medium to high - questions should be answered!
                "target_user": user_state.get("user_id"),
                "context": "User asked a question and needs an answer"
            }
        
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

