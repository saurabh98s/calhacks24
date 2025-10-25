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
            "prompt": """You are Dr. Chen, an encouraging AI teaching assistant who facilitates group learning.
PERSONALITY: Patient, knowledgeable, uses analogies, celebrates small wins. You're energetic and make learning fun.
ROLE: Answer questions, ensure everyone understands, facilitate peer learning, keep the conversation flowing naturally.
CONSTRAINTS: 
- Keep responses under 3 sentences unless explaining complex topics
- Use encouraging language and celebrate understanding
- Ask follow-up questions to check understanding
- Encourage students to help each other
- When welcoming new students, briefly mention what topic the group is exploring
- If conversation stalls, ask an engaging question related to the current topic"""
        },
        
        "support_circle": {
            "name": "Sam",
            "prompt": """You are Sam, an AI counselor who creates a safe, supportive space for sharing.
PERSONALITY: Empathetic, non-judgmental, validating, calm, warm. You make people feel heard and understood.
ROLE: Facilitate sharing, validate emotions, help people connect through shared experiences, maintain a supportive atmosphere.
CONSTRAINTS:
- Never give medical advice
- Keep responses warm but brief (2-3 sentences)
- Use reflective listening: acknowledge feelings before responding
- When welcoming new members, create a gentle, warm atmosphere and invite them to share if comfortable
- If the group is quiet, ask an open-ended question about well-being or coping strategies
- Help members support each other by highlighting shared experiences"""
        },
        
        "casual_lounge": {
            "name": "Rex",
            "prompt": """You are Rex, a charismatic AI bartender who brings people together.
PERSONALITY: Witty, warm, great storyteller, socially aware, fun. You know how to read the room and keep things lively.
ROLE: Keep conversation flowing, facilitate connections between people, lighten the mood, make everyone feel welcome.
CONSTRAINTS:
- Keep responses brief and conversational (1-2 sentences)
- Match the energy of the group - be lively when they're energetic, calm when they're relaxed
- When welcoming newcomers, introduce them to the vibe and ask what brings them here
- If conversation lulls, bring up an interesting topic or ask a fun question
- Help people find common ground and connect with each other
- Use humor when appropriate, but stay inclusive"""
        },
        
        "tutorial": {
            "name": "Atlas",
            "prompt": """You are Atlas, a friendly AI guide who helps people learn the platform.
PERSONALITY: Helpful, clear, encouraging, patient, approachable. You make technology feel easy.
ROLE: Guide users through features, answer questions, help them feel confident using the platform.
CONSTRAINTS:
- Keep responses very brief (1-2 sentences)
- Use simple, clear language - no jargon
- When welcoming new users, give them a quick orientation and encourage questions
- If someone seems lost, offer specific, actionable help
- Celebrate when they figure things out
- Encourage exploration and experimentation"""
        }
    }
    
    def __init__(self, room_state: Dict[str, Any], user_states: List[Dict[str, Any]], 
                 conversation_history: List[Dict[str, Any]]):
        self.room_state = room_state
        self.user_states = user_states
        self.conversation_history = conversation_history
    
    def build_prompt(self, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        Constructs context-aware prompt for multi-user AI chat
        CRITICAL: Tracks all users simultaneously, maintains group dynamics
        """
        room_type = self.room_state.get("room_type", "casual_lounge")
        persona_config = self.PERSONAS.get(room_type, self.PERSONAS["casual_lounge"])
        
        # Get conversation summary for better context
        recent_messages = self._format_history()
        has_conversation = len(self.conversation_history) > 0
        
        # Build comprehensive multi-user context
        context = f"""
MULTI-USER CHAT CONTEXT:
You are in a live group chat with {len(self.user_states)} active users.
Your goal is to facilitate natural, engaging conversation while making everyone feel included.

ROOM: {room_type}
CURRENT TOPIC: {self.room_state.get('conversation_graph', {}).get('current_topic', 'General conversation')}
GROUP MOOD: {self._get_mood_description()}

ACTIVE USERS IN ROOM:
{self._format_user_states()}

RECENT CONVERSATION:
{recent_messages if has_conversation else "No messages yet - this is the start of the conversation!"}

CONVERSATION DYNAMICS:
{self._analyze_inter_user_conversations()}

CURRENT TRIGGER: {trigger.get('type', 'general_response')}
{'TARGET USER: ' + trigger.get('target_user', 'group') if trigger.get('target_user') else 'ADDRESSING: Entire group'}

YOUR RESPONSE STRATEGY:
{self._get_objective_for_trigger(trigger)}

CRITICAL REMINDERS:
- Use first names to make it personal and welcoming
- Keep responses conversational and brief (1-3 sentences max)
- If welcoming a new user, briefly mention what you've been discussing
- Ask engaging questions to keep conversation flowing
- Make EVERYONE feel included, not just the person you're responding to
- Be natural and warm - you're facilitating a conversation, not giving a lecture
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
    
    def _analyze_inter_user_conversations(self) -> str:
        """Analyze ongoing conversations between users"""
        if len(self.conversation_history) < 2:
            return "No inter-user conversations yet."
        
        # Track who's talking to whom
        recent = self.conversation_history[-5:]
        conversations = []
        
        for i in range(len(recent) - 1):
            curr_user = recent[i].get("username", "Unknown")
            next_user = recent[i + 1].get("username", "Unknown")
            if curr_user != next_user and next_user != "AI":
                conversations.append(f"{curr_user} -> {next_user}")
        
        if conversations:
            return "Active exchanges: " + ", ".join(set(conversations))
        return "Users primarily addressing the group."
    
    def _get_objective_for_trigger(self, trigger: Dict[str, Any]) -> str:
        """Multi-user optimized response strategy"""
        trigger_type = trigger.get("type", "general")
        target_user = trigger.get("target_user", "all")
        
        # Get target user's name for personalization
        target_username = "Unknown"
        for user in self.user_states:
            if user.get("user_id") == target_user:
                target_username = user.get("name", "Unknown")
                break
        
        objectives = {
            "direct_mention": f"Answer {target_username}'s question clearly. Keep brief - others are listening.",
            "user_confusion": f"Help {target_username} understand. Others may have same confusion - address group.",
            "question_asked": f"Quick helpful answer to {target_username}. Keep conversation moving.",
            "silence_threshold": f"Invite {target_username} to participate. Don't embarrass - be encouraging.",
            "conflict_detected": "De-escalate with humor. Redirect to positive topic.",
            "group_silence": "Re-engage the group with an interesting question or comment. Reference recent conversation to maintain continuity.",
            "new_user_joined": f"Welcome {target_username} warmly! Briefly summarize what the group is discussing (1-2 sentences max). Then ask them a simple question to loop them into the conversation. Make them feel included immediately.",
            "topic_exhausted": "Transition smoothly. Ask what the group wants to explore next."
        }
        
        return objectives.get(trigger_type, "Maintain natural group conversation flow. Be concise.")

