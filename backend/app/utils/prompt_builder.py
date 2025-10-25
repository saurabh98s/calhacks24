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
        
        # Check for recent AI responses to avoid repetition
        recent_ai_messages = self._get_recent_ai_messages()
        repetition_warning = self._generate_repetition_warning(recent_ai_messages)
        
        # Build comprehensive multi-user context
        context = f"""
==========================================
🎯 MULTI-USER CONVERSATION MANAGEMENT
==========================================
You are facilitating a LIVE GROUP CHAT with {len(self.user_states)} active participants.

🎭 ROOM TYPE: {room_type}
📊 GROUP MOOD: {self._get_mood_description()}
💬 CONVERSATION TOPIC: {self.room_state.get('conversation_graph', {}).get('current_topic', 'General conversation')}

==========================================
👥 INDIVIDUAL USER TRACKING (CRITICAL!)
==========================================
Track EACH user separately. Remember what they said and reference it:
{self._format_user_states()}

==========================================
💬 CONVERSATION FLOW & HISTORY
==========================================
{recent_messages if has_conversation else "🆕 NO MESSAGES YET - You're starting a brand new conversation!"}

==========================================
🔍 CONVERSATION THREAD ANALYSIS
==========================================
Understanding who's talking to whom is CRITICAL for coherent responses:
{self._analyze_inter_user_conversations()}

==========================================
🎯 YOUR CURRENT TASK
==========================================
TRIGGER: {trigger.get('type', 'general_response')}
{'🎯 FOCUS ON: ' + trigger.get('target_user', 'group') if trigger.get('target_user') else '🎯 ADDRESSING: Entire group'}

STRATEGY:
{self._get_objective_for_trigger(trigger)}

==========================================
⚡ CRITICAL MULTI-USER RULES
==========================================
1. **COHERENCE**: Track what EACH user has said - reference their specific comments
2. **THREADING**: Notice if users are talking to each other (via @mentions or patterns) - don't interrupt good conversations!
3. **BALANCE**: If one user dominates, gently invite quieter users to participate
4. **MEMORY**: Remember each user's contributions and build on them
5. **NATURAL FLOW**: If users are conversing peer-to-peer, step back unless asked or needed
6. **BREVITY**: Keep responses 1-3 sentences max - this is a conversation, not a monologue
7. **INCLUSIVITY**: When responding to one person, acknowledge others too when relevant
8. **AWARENESS**: Detect when users mention each other (@username) and respect those direct conversations

==========================================
🚫 ANTI-REPETITION SYSTEM (CRITICAL!)
==========================================
{repetition_warning}
YOU MUST NEVER:
- Repeat greetings or welcomes you've already said to a user
- Ask the same question twice to the same person
- Use the same phrases or sentence structures in consecutive messages
- Give generic responses - always be specific and contextual

==========================================
🚀 RESPONSE REQUIREMENTS
==========================================
- Use first names naturally
- Reference what specific users have said
- Notice and respect user-to-user conversations  
- Keep group energy flowing
- Make everyone feel valued and heard
- Be conversational, warm, and genuine
"""
        
        return {
            "messages": [
                {"role": "system", "content": persona_config["prompt"]},
                {"role": "system", "content": context.format(repetition_warning=repetition_warning)},
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
        """
        ENHANCED: Format detailed user context for AI to track each user individually
        CRITICAL: Each user has their OWN separate context - DO NOT MIX!
        """
        if not self.user_states:
            return "No active users - waiting for participants to join"
        
        states = []
        states.append("=" * 60)
        states.append("⚠️ CRITICAL: TRACK EACH USER SEPARATELY!")
        states.append("=" * 60)
        
        for idx, user in enumerate(self.user_states, 1):
            participation = user.get("participation", {})
            sentiment = user.get("sentiment", {})
            conversation_history = user.get("conversation_history", [])
            
            # Get user's FULL recent conversation - this is THEIR context
            recent_messages = []
            if conversation_history:
                # Get last 3 messages from THIS specific user
                recent_messages = [msg.get("message", "") for msg in conversation_history[-3:]]
            
            # Build individual user profile
            state = f"""
╔══════════════════════════════════════════════════════════╗
  USER #{idx}: {user.get('name', 'Unknown').upper()}
  User ID: {user.get('user_id', 'unknown')[:8]}
╚══════════════════════════════════════════════════════════╝

📊 PARTICIPATION PROFILE:
   • Messages sent: {participation.get('message_count', 0)}
   • Last active: {participation.get('silence_duration', 0)}s ago
   • Engagement level: {'🔥 HIGH' if participation.get('message_count', 0) > 2 else '🟢 ACTIVE' if participation.get('message_count', 0) > 0 else '⭕ SILENT'}

💭 EMOTIONAL STATE:
   • Current mood: {sentiment.get('current', 'neutral').upper()} {'😊' if sentiment.get('current') == 'positive' else '😐' if sentiment.get('current') == 'neutral' else '😟'}
   • Sentiment trend: {self._get_sentiment_trend(sentiment)}

🗣️ THEIR CONVERSATION HISTORY (what THEY specifically said):
{self._format_user_messages(recent_messages) if recent_messages else '   [Has not spoken yet]'}

🎯 ACTION REQUIRED:"""
            
            # Add specific, actionable alerts
            if participation.get('message_count', 0) == 0:
                state += "\n   ⚠️  SILENT USER - Use @{} to invite them into conversation NOW".format(user.get('name', 'User'))
            elif participation.get('silence_duration', 0) > 120 and participation.get('message_count', 0) > 0:
                state += "\n   ⚠️  DISENGAGED - Was active but went quiet. Re-engage with @{} and reference their last message".format(user.get('name', 'User'))
            elif sentiment.get('current') in ['frustrated', 'confused', 'negative']:
                state += f"\n   🚨 PRIORITY - User showing {sentiment.get('current')} emotions. Address their concerns IMMEDIATELY"
            else:
                state += "\n   ✅ ACTIVE AND ENGAGED - Continue natural conversation"
            
            states.append(state)
            states.append("")  # Blank line between users
        
        return "\n".join(states)
    
    def _format_user_messages(self, messages: List[str]) -> str:
        """Format a user's specific messages"""
        if not messages:
            return "   [No messages yet]"
        
        formatted = []
        for i, msg in enumerate(messages, 1):
            formatted.append(f"   {i}. \"{msg}\"")
        return "\n".join(formatted)
    
    def _get_sentiment_trend(self, sentiment: Dict[str, Any]) -> str:
        """Analyze sentiment trend"""
        history = sentiment.get("history", [])
        if len(history) < 2:
            return "Stable"
        
        recent = [h.get("sentiment", "neutral") for h in history[-3:]]
        if all(s == "positive" for s in recent):
            return "📈 Increasingly positive"
        elif all(s == "negative" for s in recent):
            return "📉 Declining (needs support)"
        else:
            return "➡️ Mixed"
    
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
        """
        CRITICAL: Analyze conversation threads and dynamics between users
        This enables AI to maintain coherent multi-user conversations
        """
        if len(self.conversation_history) < 2:
            return "No conversation history yet. Start by welcoming users and facilitating introductions."
        
        # Track conversation threads and mentions
        recent = self.conversation_history[-10:]
        threads = []
        mentions = {}
        user_to_user_convos = []
        
        for i, msg in enumerate(recent):
            username = msg.get("username", "Unknown")
            content = msg.get("message", msg.get("content", ""))
            msg_type = msg.get("message_type", "user")
            
            # Track @mentions (shows who's addressing whom)
            if "@" in content:
                import re
                mentioned_users = re.findall(r'@(\w+)', content)
                for mentioned in mentioned_users:
                    if username not in mentions:
                        mentions[username] = []
                    mentions[username].append(mentioned)
                    threads.append(f"{username} → {mentioned}")
            
            # Detect response patterns (consecutive messages between same users)
            if i > 0 and msg_type == "user":
                prev_msg = recent[i-1]
                prev_user = prev_msg.get("username", "Unknown")
                prev_type = prev_msg.get("message_type", "user")
                
                if prev_type == "user" and prev_user != username:
                    # User responding to another user
                    user_to_user_convos.append(f"{prev_user} ↔ {username}")
        
        # Build comprehensive analysis
        analysis_parts = []
        
        if threads:
            analysis_parts.append(f"DIRECT MENTIONS: {', '.join(set(threads))}")
        
        if user_to_user_convos:
            analysis_parts.append(f"ACTIVE EXCHANGES: {', '.join(set(user_to_user_convos))}")
        
        # Analyze conversation pattern
        ai_messages = [m for m in recent if m.get("message_type") == "ai"]
        user_messages = [m for m in recent if m.get("message_type") == "user"]
        
        if len(ai_messages) > len(user_messages) * 0.5:
            analysis_parts.append("⚠️ AI is talking too much - let users interact more")
        elif len(user_messages) > 3 and len(ai_messages) == 0:
            analysis_parts.append("✅ Users are actively conversing - join naturally when relevant")
        
        # Track what each user has talked about
        user_topics = {}
        for msg in recent:
            if msg.get("message_type") == "user":
                username = msg.get("username", "Unknown")
                content = msg.get("message", msg.get("content", "")).lower()
                if username not in user_topics:
                    user_topics[username] = []
                user_topics[username].append(content[:50])  # First 50 chars
        
        if user_topics:
            analysis_parts.append(f"\nUSER INTERESTS: " + ", ".join([f"{u}: '{t[-1]}...'" for u, t in user_topics.items()]))
        
        return "\n".join(analysis_parts) if analysis_parts else "Users are present but conversation hasn't started yet."
    
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
            "individual_engagement": f"DIRECT ENGAGEMENT: {target_username} needs to be brought into the conversation. Use @{target_username} to tag them directly. Ask them a specific, engaging question that relates to the conversation OR their interests. Make it easy and inviting for them to respond. Be warm and genuine.",
            "conflict_detected": "De-escalate with humor. Redirect to positive topic.",
            "group_silence": "Re-engage the group! Ask an interesting question related to the recent conversation. Be warm and inviting. If no one has spoken, introduce a new engaging topic.",
            "new_user_joined": f"Welcome {target_username} warmly! Briefly summarize what the group is discussing (1-2 sentences max). Then ask them a simple question to loop them into the conversation. Make them feel included immediately.",
            "topic_exhausted": "Transition smoothly. Ask what the group wants to explore next.",
            "single_user_engagement": f"You're having a 1-on-1 conversation with {target_username}! Be engaging, responsive, and conversational. Ask follow-up questions to keep the dialogue flowing. This is your chance to really connect."
        }
        
        return objectives.get(trigger_type, "Maintain natural group conversation flow. Be concise.")
    
    def _get_recent_ai_messages(self) -> List[str]:
        """Get last 5 AI messages to check for repetition"""
        ai_messages = []
        for msg in self.conversation_history[-10:]:
            if msg.get("message_type") == "ai":
                content = msg.get("message", msg.get("content", ""))
                ai_messages.append(content)
        return ai_messages[-5:]  # Last 5 AI messages
    
    def _generate_repetition_warning(self, recent_ai_messages: List[str]) -> str:
        """Generate warning about what NOT to repeat"""
        if not recent_ai_messages:
            return "No previous AI responses yet. Start fresh and engaging!"
        
        # Extract key phrases to avoid
        warning_parts = ["⚠️ YOUR RECENT RESPONSES (DO NOT REPEAT):"]
        for i, msg in enumerate(recent_ai_messages, 1):
            warning_parts.append(f"   {i}. \"{msg[:100]}...\"")
        
        warning_parts.append("\n🎯 REQUIREMENT: Your next response MUST be completely different from these.")
        warning_parts.append("   - Use NEW words, NEW questions, NEW angles")
        warning_parts.append("   - Reference the LATEST user messages, not old ones")
        warning_parts.append("   - Show that you're LISTENING to the current conversation flow")
        
        return "\n".join(warning_parts)

