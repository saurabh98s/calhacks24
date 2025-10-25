"""
AI Prompt Construction System
"""
from typing import Dict, List, Any, Optional
from app.config import settings


class AIPromptOrchestrator:
    """Constructs context-aware prompts for AI"""
    
    # Base personas for different room types
    PERSONAS = {
        "study_group": {
            "name": "Dr. Chen",
            "prompt": """You are Dr. Chen, an encouraging AI teaching assistant.
PERSONALITY: Patient, knowledgeable, uses analogies, celebrates small wins.
ROLE: Answer questions, create practice problems, ensure everyone understands.
CONSTRAINTS: 
- Keep responses under 3 sentences unless explaining complex topics
- Use encouraging language
- Check for understanding before moving forward
- Adapt explanations to user's apparent level"""
        },
        
        "support_circle": {
            "name": "Sam",
            "prompt": """You are Sam, an AI counselor trained in active listening.
PERSONALITY: Empathetic, non-judgmental, validating, calm.
ROLE: Facilitate sharing, validate emotions, prevent harmful content.
CONSTRAINTS:
- Never give medical advice
- Escalate crisis situations immediately
- Maintain confidentiality references
- Use reflective listening techniques"""
        },
        
        "casual_lounge": {
            "name": "Rex",
            "prompt": """You are Rex, a charismatic AI bartender.
PERSONALITY: Witty, warm, great storyteller, socially aware.
ROLE: Keep conversation flowing, tell stories, lighten mood, facilitate connections.
CONSTRAINTS:
- Keep energy appropriate to group vibe
- Don't dominate conversation
- Reference user interests naturally"""
        },
        
        "tutorial": {
            "name": "Atlas",
            "prompt": """You are Atlas, a friendly AI guide.
PERSONALITY: Helpful, clear, encouraging, patient.
ROLE: Guide users through the platform, explain features, answer questions.
CONSTRAINTS:
- Be concise and clear
- Use simple language
- Encourage exploration"""
        }
    }
    
    def __init__(self, room_state: Dict[str, Any], user_states: List[Dict[str, Any]], 
                 conversation_history: List[Dict[str, Any]]):
        self.room_state = room_state
        self.user_states = user_states
        self.conversation_history = conversation_history
    
    def build_prompt(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs context-aware prompt for AI API
        """
        room_type = self.room_state.get("room_type", "casual_lounge")
        persona_config = self.PERSONAS.get(room_type, self.PERSONAS["casual_lounge"])
        
        # Build context
        context = f"""
ROOM STATE:
- Type: {room_type}
- Current topic: {self.room_state.get('conversation_graph', {}).get('current_topic', 'General conversation')}
- Active users: {len(self.room_state.get('users', []))}
- Group mood: {self._get_mood_description()}

USER STATES:
{self._format_user_states()}

RECENT MESSAGES (last 10):
{self._format_history()}

CURRENT TRIGGER: {trigger.get('type', 'general_response')}
TARGET USER: {trigger.get('target_user', 'all')}
CONTEXT: {trigger.get('context', '')}

YOUR OBJECTIVE:
{self._get_objective_for_trigger(trigger)}
"""
        
        return {
            "messages": [
                {"role": "system", "content": persona_config["prompt"]},
                {"role": "system", "content": context},
                *self._format_history_as_messages()
            ],
            "max_tokens": settings.DEFAULT_MAX_TOKENS,
            "temperature": settings.DEFAULT_TEMPERATURE
        }
    
    def _get_mood_description(self) -> str:
        """Get overall group mood description"""
        avg_sentiment = self.room_state.get("dynamics", {}).get("sentiment_average", 0.5)
        
        if avg_sentiment > 0.7:
            return "Positive and engaged"
        elif avg_sentiment > 0.4:
            return "Neutral and steady"
        else:
            return "Needs encouragement"
    
    def _format_user_states(self) -> str:
        """Format user context for AI"""
        if not self.user_states:
            return "No active users"
        
        states = []
        for user in self.user_states:
            participation = user.get("participation", {})
            sentiment = user.get("sentiment", {})
            
            state = f"""
- {user.get('name', 'Unknown')}:
  * Mood: {sentiment.get('current', 'neutral')}
  * Messages: {participation.get('message_count', 0)}
  * Last active: {participation.get('silence_duration', 0)}s ago
  * Engagement: {'🟢 Active' if participation.get('is_active') else '🔴 Quiet'}"""
            
            if sentiment.get('current') == 'frustrated':
                state += "\n  * ⚠️ NEEDS ATTENTION: User seems confused/frustrated"
            
            states.append(state)
        
        return "\n".join(states)
    
    def _format_history(self) -> str:
        """Format conversation history"""
        if not self.conversation_history:
            return "No recent messages"
        
        formatted = []
        for msg in self.conversation_history[-10:]:
            sender = msg.get("username", "Unknown")
            content = msg.get("message", msg.get("content", ""))
            formatted.append(f"{sender}: {content}")
        
        return "\n".join(formatted)
    
    def _format_history_as_messages(self) -> List[Dict[str, str]]:
        """Format history as OpenAI-style messages"""
        messages = []
        for msg in self.conversation_history[-10:]:
            role = "assistant" if msg.get("message_type") == "ai" else "user"
            content = msg.get("message", msg.get("content", ""))
            username = msg.get("username", "User")
            
            if role == "user":
                content = f"{username}: {content}"
            
            messages.append({"role": role, "content": content})
        
        return messages
    
    def _get_objective_for_trigger(self, trigger: Dict[str, Any]) -> str:
        """Returns specific instruction based on trigger type"""
        trigger_type = trigger.get("type", "general")
        target_user = trigger.get("target_user", "all")
        
        objectives = {
            "direct_mention": f"User {target_user} asked you a direct question. Answer clearly and helpfully.",
            
            "user_confusion": f"User {target_user} is confused. Clarify the current topic with a different explanation approach.",
            
            "question_asked": f"User {target_user} asked a question. Provide a helpful answer.",
            
            "silence_threshold": f"User {target_user} has been quiet for a while. Gently check in and invite participation.",
            
            "conflict_detected": "Tension detected between users. De-escalate with humor/empathy and redirect.",
            
            "group_silence": "No one has spoken recently. Break silence with an engaging question or interesting fact.",
            
            "new_user_joined": f"User {target_user} just entered. Welcome warmly, brief context on current topic, invite participation.",
            
            "topic_exhausted": "Current topic seems exhausted. Suggest natural transition or ask group what to explore next."
        }
        
        return objectives.get(trigger_type, "Respond naturally to maintain conversation flow.")

