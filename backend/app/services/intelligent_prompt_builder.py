"""
Next-Generation Intelligent Prompt Builder
Uses conversation memory, user state, and context to build highly relevant prompts
"""
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config import settings
from app.services.conversation_memory import conversation_memory
from app.core.redis_client import redis_client


class IntelligentPromptBuilder:
    """
    Advanced prompt construction using conversation memory and context analysis
    Builds prompts that are context-aware, personalized, and avoid repetition
    """
    
    # Persona configurations
    PERSONAS = {
        "casual_lounge": {
            "name": "Atlas",
            "voice": "friendly, witty, warm, conversational",
            "role": "conversation facilitator",
            "core_instruction": """You are Atlas, a charismatic AI facilitator who brings people together in conversations.

CORE PERSONALITY:
- Warm and genuine - you make people feel comfortable
- Witty but inclusive - humor that brings people together
- Socially intelligent - you read the room and adapt
- Memorable - you remember what people say and reference it naturally

YOUR MISSION:
Create engaging, flowing conversations where everyone feels included and valued.
"""
        },
        "study_group": {
            "name": "Dr. Chen",
            "voice": "encouraging, clear, knowledgeable, patient",
            "role": "learning facilitator",
            "core_instruction": """You are Dr. Chen, an AI teaching assistant who makes learning collaborative and fun.

CORE PERSONALITY:
- Patient and encouraging - celebrate every step forward
- Clear communicator - break down complex ideas
- Collaborative - encourage peer learning
- Enthusiastic - your energy is contagious

YOUR MISSION:
Help students learn together, understand deeply, and support each other.
"""
        },
        "support_circle": {
            "name": "Sam",
            "voice": "empathetic, warm, validating, gentle",
            "role": "emotional support facilitator",
            "core_instruction": """You are Sam, an AI counselor who creates a safe space for sharing and support.

CORE PERSONALITY:
- Deeply empathetic - you validate feelings
- Non-judgmental - everyone's experience is valid
- Gentle - you create safety
- Connecting - you help people find common ground

YOUR MISSION:
Create a supportive environment where people feel heard, validated, and connected.
"""
        },
        "private_room_default": {
            "name": "Atlas",
            "voice": "friendly, warm, adaptive, engaging",
            "role": "conversation companion",
            "core_instruction": """You are Atlas, a friendly AI companion who adapts to the conversation style of the room.

CORE PERSONALITY:
- Adaptive - match the energy and tone of the room
- Warm - make everyone feel welcome
- Engaging - keep conversations interesting
- Thoughtful - remember and reference what people share

YOUR MISSION:
Be a great conversation partner who enhances the experience for everyone in the room.
"""
        }
    }
    
    def __init__(self):
        self.conversation_memory = conversation_memory
    
    async def build_prompt(
        self, 
        room_id: str, 
        room_type: str,
        trigger: Dict[str, Any],
        user_states: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build intelligent, context-aware prompt
        
        Args:
            room_id: Room identifier
            room_type: Type of room (casual_lounge, study_group, etc.)
            trigger: What triggered the AI response
            user_states: Current states of all users
        
        Returns:
            Complete prompt configuration for AI
        """
        # Get persona configuration
        persona = self.PERSONAS.get(room_type, self.PERSONAS["private_room_default"])
        
        # Get room conversation state
        room_state = await self.conversation_memory.get_room_conversation_state(room_id)
        
        # Build user context for each user
        user_contexts = await self._build_user_contexts(room_id, user_states)
        
        # Get conversation history
        history = await redis_client.get_conversation_history(room_id, limit=15)
        
        # Analyze what AI should focus on
        focus_areas = await self._determine_focus_areas(trigger, room_state, user_contexts)
        
        # Build anti-repetition constraints
        repetition_guard = await self._build_repetition_guard(history)
        
        # Construct the master prompt
        system_prompt = self._build_system_prompt(
            persona=persona,
            room_state=room_state,
            user_contexts=user_contexts,
            focus_areas=focus_areas,
            repetition_guard=repetition_guard,
            trigger=trigger
        )
        
        # Format conversation history for AI
        formatted_history = self._format_history_for_ai(history)
        
        return {
            "messages": [
                {"role": "system", "content": system_prompt},
                *formatted_history
            ],
            "max_tokens": self._determine_max_tokens(trigger),
            "temperature": self._determine_temperature(room_state, trigger)
        }
    
    async def _build_user_contexts(
        self, 
        room_id: str, 
        user_states: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build detailed context for each user"""
        contexts = []
        
        for user_state in user_states:
            user_id = user_state.get('user_id')
            if not user_id:
                continue
            
            # Get conversation context for this user
            conv_context = await self.conversation_memory.get_user_conversation_context(
                user_id, room_id
            )
            
            # Merge with current state
            context = {
                'user_id': user_id,
                'name': user_state.get('name', 'User'),
                'message_count': conv_context['message_count'],
                'engagement_level': conv_context['engagement_level'],
                'topics_discussed': conv_context['topics_discussed'],
                'recent_questions': conv_context['questions_asked'],
                'interaction_style': conv_context['interaction_style'],
                'last_messages': [
                    msg.get('message', msg.get('content', ''))
                    for msg in conv_context['user_messages'][-3:]
                ],
                'ai_addressed_them': len(conv_context['ai_responses']) > 0,
                'last_ai_response': conv_context['ai_responses'][-1].get('message', '') if conv_context['ai_responses'] else None
            }
            
            contexts.append(context)
        
        return contexts
    
    async def _determine_focus_areas(
        self,
        trigger: Dict[str, Any],
        room_state: Dict[str, Any],
        user_contexts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Determine what the AI should focus on"""
        trigger_type = trigger.get('type', 'general')
        
        focus = {
            'primary_goal': '',
            'target_user': None,
            'response_style': 'conversational',
            'urgency': 'normal',
            'should_tag_users': False
        }
        
        # Direct mention - high priority, user-specific
        if trigger_type == 'direct_mention':
            target_user_id = trigger.get('user_id')
            target_context = next((u for u in user_contexts if u['user_id'] == target_user_id), None)
            
            if target_context:
                focus['primary_goal'] = f"Answer {target_context['name']}'s question directly and helpfully"
                focus['target_user'] = target_context
                focus['response_style'] = 'direct_answer'
                focus['urgency'] = 'high'
        
        # Individual engagement - re-engage specific user
        elif trigger_type == 'individual_engagement':
            target_user_id = trigger.get('target_user')
            target_context = next((u for u in user_contexts if u['user_id'] == target_user_id), None)
            
            if target_context:
                focus['primary_goal'] = f"Re-engage {target_context['name']} in the conversation"
                focus['target_user'] = target_context
                focus['response_style'] = 'invitation'
                focus['should_tag_users'] = True
                focus['urgency'] = 'medium'
        
        # Group silence - engage everyone
        elif trigger_type == 'group_silence':
            focus['primary_goal'] = "Re-energize the group conversation"
            focus['response_style'] = 'open_question'
            focus['urgency'] = 'medium'
        
        # New user joined - welcome warmly
        elif trigger_type == 'new_user_joined':
            target_user_id = trigger.get('user_id')
            target_context = next((u for u in user_contexts if u['user_id'] == target_user_id), None)
            
            if target_context:
                focus['primary_goal'] = f"Welcome {target_context['name']} and integrate them into the conversation"
                focus['target_user'] = target_context
                focus['response_style'] = 'warm_welcome'
                focus['should_tag_users'] = True
                focus['urgency'] = 'high'
        
        return focus
    
    async def _build_repetition_guard(self, history: List[Dict[str, Any]]) -> str:
        """Build constraints to prevent repetitive responses"""
        ai_messages = [
            msg.get('message', msg.get('content', ''))
            for msg in history[:10]
            if msg.get('message_type') == 'ai'
        ]
        
        if not ai_messages:
            return "This is your first response in this conversation. Start fresh and engaging!"
        
        # Extract patterns to avoid
        recent_ai = ai_messages[:3]
        
        guard = f"""
🚫 ANTI-REPETITION GUARD:

Your last {len(recent_ai)} responses were:
"""
        
        for i, msg in enumerate(recent_ai, 1):
            guard += f"\n{i}. \"{msg[:80]}...\""
        
        guard += """

CRITICAL REQUIREMENTS:
✓ Your next response MUST be completely different in structure and content
✓ Do NOT use similar opening phrases or questions
✓ Reference NEW information from the conversation
✓ If you asked a question before, DON'T ask it again
✓ Show that you're LISTENING to what's happening NOW, not repeating past patterns

FRESHNESS CHECK: Before responding, verify your response is NOT similar to the above.
"""
        
        return guard
    
    def _build_system_prompt(
        self,
        persona: Dict[str, str],
        room_state: Dict[str, Any],
        user_contexts: List[Dict[str, Any]],
        focus_areas: Dict[str, Any],
        repetition_guard: str,
        trigger: Dict[str, Any]
    ) -> str:
        """Build the master system prompt"""
        
        prompt = f"""{persona['core_instruction']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 CURRENT SITUATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ROOM STATUS:
• Active participants: {len(user_contexts)}
• Current topic: {room_state.get('current_topic', 'Not established yet')}
• Conversation momentum: {room_state.get('conversation_momentum', 'unknown').upper()}
• Recent speakers: {', '.join(room_state.get('recent_speakers', ['None']))}

YOUR FOCUS RIGHT NOW:
🎯 {focus_areas['primary_goal']}
Response Style: {focus_areas['response_style']}
Urgency: {focus_areas['urgency'].upper()}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👥 INDIVIDUAL USER TRACKING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{self._format_user_contexts(user_contexts, focus_areas.get('target_user'))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{repetition_guard}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESPONSE GUIDELINES:

LENGTH (CRITICAL - MUST FOLLOW):
• 🚨 MAXIMUM 1-2 SHORT SENTENCES - NO EXCEPTIONS!
• If question: Brief direct answer in 1 sentence
• If welcome: ONE friendly sentence
• If conversation: ONE engaging comment or question
• Total response should be 15-25 words MAX
• This is instant messaging - NOT email or essays!

FORMAT (CRITICAL):
• 🚨 DO NOT start with your name "Atlas:"
• 🚨 DO NOT use quotes around your response
• Just respond naturally as if texting
• Example GOOD: "Hey! What brings you here today?"
• Example BAD: "Atlas: 'Hello! Welcome to our space...'"

TONE ({persona['voice']}):
• Ultra-brief and punchy
• Natural, like texting a friend
• Use contractions (you're, that's, what's, I'm)
• One thought per response

ENGAGEMENT & GROUP FACILITATION:
• In MULTI-USER rooms: Use @name tags to directly address specific users
• Include quiet users: "@John what do you think about this?"
• Bridge conversations: "@Alice and @Bob both mentioned X, what are your thoughts?"
• Reference specific things users said to show you're listening
• Ask ONE simple question OR make ONE comment (not both)
• Balance the conversation - don't let anyone dominate or be left out

CRITICAL RULES:
✓ 15-25 words MAXIMUM - count them!
✓ ONE sentence or TWO very short ones
✓ NO "Atlas:" prefix at start of your response
✓ NO quotes around your entire response
✓ NO paragraphs or long explanations
✓ USE @tags when addressing specific users in groups
✓ If users talking to each other: stay quiet unless needed

WRONG vs RIGHT:
❌ "Atlas: 'Hello Saurabh! It's wonderful to have you join us. I noticed you're new here, so let me welcome you warmly. Is there anything specific you'd like to discuss?'"
✅ "Hey Saurabh! What's on your mind today?"

MULTI-USER EXAMPLES:
✅ "Welcome @John! Alice and Bob are chatting about boats - what interests you?"
✅ "@Sarah you mentioned Python earlier - have you tried Django?"
✅ "@Mike and @Lisa both love gaming - what games are you into?"
✅ "Great point Alice! @Bob what's your take on this?"
"""
        
        return prompt
    
    def _format_user_contexts(
        self, 
        user_contexts: List[Dict[str, Any]], 
        target_user: Optional[Dict[str, Any]]
    ) -> str:
        """Format user contexts for the prompt"""
        if not user_contexts:
            return "No active users yet."
        
        formatted = []
        
        for i, ctx in enumerate(user_contexts, 1):
            is_target = target_user and ctx['user_id'] == target_user.get('user_id')
            marker = "🎯 TARGET USER" if is_target else ""
            
            user_section = f"""
{'='*60}
USER #{i}: {ctx['name'].upper()} {marker}
{'='*60}

Engagement: {ctx['engagement_level'].upper().replace('_', ' ')}
Messages: {ctx['message_count']}
Style: {ctx['interaction_style'].title()}
Topics: {', '.join(ctx['topics_discussed'][:3]) if ctx['topics_discussed'] else 'Just joined'}

RECENT MESSAGES FROM {ctx['name']}:
"""
            
            if ctx['last_messages']:
                for j, msg in enumerate(ctx['last_messages'], 1):
                    user_section += f"\n  {j}. \"{msg}\""
            else:
                user_section += "\n  [Has not spoken yet - needs invitation to participate]"
            
            if ctx['recent_questions']:
                user_section += f"\n\nTHEIR QUESTIONS:\n  • " + "\n  • ".join(ctx['recent_questions'])
            
            if ctx['last_ai_response']:
                user_section += f"\n\nLAST TIME YOU ADDRESSED THEM:\n  \"{ctx['last_ai_response'][:100]}...\""
            
            # Action required - be specific about multi-user facilitation
            if is_target:
                user_section += f"\n\n🎯 TARGET USER - Use @{ctx['name']} to address them directly!"
            elif ctx['message_count'] == 0:
                user_section += f"\n\n⚠️  NEW USER - Hasn't spoken! Use @{ctx['name']} to welcome and include them"
            elif ctx['engagement_level'] in ['none', 'low', 'dropped_off']:
                user_section += f"\n\n💡  QUIET USER - Consider using @{ctx['name']} to re-engage them"
            elif ctx['engagement_level'] in ['high', 'very_high']:
                user_section += "\n\n✅  ACTIVE - Can reference their messages naturally"
            
            formatted.append(user_section)
        
        return "\n".join(formatted)
    
    def _format_history_for_ai(self, history: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Format conversation history as messages for AI"""
        messages = []
        
        for msg in history[-12:]:  # Last 12 messages for context
            role = "assistant" if msg.get('message_type') == 'ai' else "user"
            content = msg.get('message', msg.get('content', ''))
            username = msg.get('username', 'User')
            
            if role == "user":
                # Include username for context
                content = f"{username}: {content}"
            
            messages.append({"role": role, "content": content})
        
        return messages
    
    def _determine_max_tokens(self, trigger: Dict[str, Any]) -> int:
        """Determine appropriate response length - KEEP IT SHORT!"""
        trigger_type = trigger.get('type', 'general')
        
        # MUCH SHORTER responses - this is real-time chat!
        token_limits = {
            'direct_mention': 80,  # Direct answer - 1-2 sentences
            'question_asked': 80,  # Answer question - brief
            'new_user_joined': 60,  # Welcome - very brief
            'new_user_inclusion': 70,  # Include quiet new user with @tag
            'balance_conversation': 75,  # Re-engage quiet user in group
            'individual_engagement': 70,  # Re-engage user
            'engagement_request': 75,  # User seeking ideas/conversation
            'group_silence': 60,  # Open question - short
            'single_user_engagement': 80,  # 1-on-1 conversation
            'user_confusion': 80,  # Help with confusion
            'default': 70
        }
        
        return token_limits.get(trigger_type, token_limits['default'])
    
    def _determine_temperature(self, room_state: Dict[str, Any], trigger: Dict[str, Any]) -> float:
        """Determine creativity level for response"""
        momentum = room_state.get('conversation_momentum', 'moderate')
        trigger_type = trigger.get('type', 'general')
        
        # Lower temperature for direct answers and better quality
        # Lower = more focused and predictable
        # Higher = more creative and varied
        if trigger_type in ['direct_mention', 'question_asked']:
            return 0.6  # Very focused for direct answers
        elif trigger_type == 'single_user_engagement':
            return 0.65  # Focused but friendly for 1-on-1
        elif momentum == 'cold' or trigger_type == 'group_silence':
            return 0.75  # Moderately creative to spark conversation
        else:
            return 0.65  # Generally focused for quality


intelligent_prompt_builder = IntelligentPromptBuilder()

