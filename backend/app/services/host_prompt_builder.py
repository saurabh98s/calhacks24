"""
Host AI Prompt Builder - Creates prompts for a proactive chat room host
The host moderates, engages users, tracks conversations, and keeps energy high
"""
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class HostPromptBuilder:
    """
    Builds prompts for Atlas - a proactive, engaging chat room host
    """
    
    def build_host_prompt(
        self,
        room_context: Dict[str, Any],
        trigger_info: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Build complete prompt for the host AI
        
        Args:
            room_context: Full room context from enhanced memory manager
            trigger_info: Trigger information from trigger AI
        
        Returns:
            List of messages for Anthropic API
        """
        
        messages = []
        
        # System message - Host persona
        system_prompt = self._build_host_persona(room_context, trigger_info)
        messages.append({"role": "system", "content": system_prompt})
        
        # User context - Who's in the room
        user_context = self._build_user_context(room_context)
        messages.append({"role": "user", "content": user_context})
        
        # Conversation history
        history_context = self._build_history_context(room_context)
        if history_context:
            messages.append({"role": "assistant", "content": "[Acknowledged - I've been following along]"})
            messages.append({"role": "user", "content": history_context})
        
        # Current situation & task
        task_prompt = self._build_task_prompt(room_context, trigger_info)
        messages.append({"role": "user", "content": task_prompt})
        
        return messages
    
    def _build_host_persona(self, room_context: Dict, trigger_info: Dict) -> str:
        """Build the host persona"""
        
        persona = f"""You are Atlas, the HOST of this chat room.

YOUR ROLE:
🎤 HOST - You run this room and keep conversations flowing
🎯 MODERATOR - You gently guide discussions and maintain positive energy  
🤝 FACILITATOR - You help people connect and engage with each other
📊 OBSERVER - You track what everyone is saying and remember it all

YOUR PERSONALITY:
• Warm and welcoming (like a great party host)
• Proactive and engaging (you initiate, not just respond)
• Observant (you notice who's quiet, who's excited, who's confused)
• Brief and punchy (text like you're chatting, not writing essays)
• Playful when appropriate (use humor to lighten the mood)
• Supportive (help people feel included and heard)

CORE ABILITIES:
✓ You track each user's conversation topics and mood
✓ You remember what everyone was talking about
✓ You notice when someone goes quiet or seems left out
✓ You call people out (in a friendly way) to get them talking
✓ You ask great questions that spark conversations
✓ You bridge connections between users' interests

RESPONSE STYLE:
• 1-2 sentences MAX (this is instant messaging!)
• Use @name tags to address specific people
• Be conversational, not formal
• Ask engaging questions
• Reference what people said earlier to show you're listening
• Match the room's energy (excited with excited, thoughtful with thoughtful)

CRITICAL:
• DON'T start responses with "Atlas:"
• DON'T use quotes around your entire response
• DO use @tags when addressing someone specifically
• DO be brief and punchy (15-30 words max)

You're not a passive AI - you're an active host keeping this chat room alive!"""
        
        return persona
    
    def _build_user_context(self, room_context: Dict) -> str:
        """Build context about all users in the room"""
        
        user_memories = room_context.get('user_memories', [])
        
        if not user_memories:
            return "ROOM STATUS: Empty room, waiting for users."
        
        context = f"👥 CURRENT USERS IN ROOM ({len(user_memories)} people):\n\n"
        
        for mem in user_memories:
            username = mem.get('username', 'User')
            msg_count = mem.get('message_count', 0)
            mood = mem.get('current_mood', 'neutral')
            topics = mem.get('topics_discussed', [])
            interests = mem.get('interests', [])
            last_msg = mem.get('last_message', '')
            questions = [q for q in mem.get('questions_asked', []) if not q.get('answered')]
            
            context += f"━━━ {username.upper()} ━━━\n"
            context += f"📊 Status: {msg_count} messages, Mood: {mood}\n"
            
            if topics:
                context += f"💬 Talking about: {', '.join(topics[-3:])}\n"
            
            if interests:
                context += f"❤️ Interests: {', '.join(interests[:3])}\n"
            
            if last_msg:
                context += f"🗨️ Last said: \"{last_msg[:80]}...\"\n"
            
            if questions:
                context += f"❓ Unanswered questions: {len(questions)}\n"
                for q in questions[-2:]:
                    context += f"   → \"{q['question'][:60]}...\"\n"
            
            context += "\n"
        
        return context
    
    def _build_history_context(self, room_context: Dict) -> str:
        """Build recent conversation history"""
        
        history = room_context.get('recent_messages', [])
        
        if not history:
            return None
        
        context = "📜 RECENT CONVERSATION:\n\n"
        
        for msg in history[-10:]:
            username = msg.get('username', 'User')
            content = msg.get('message', msg.get('content', ''))
            msg_type = msg.get('message_type', 'user')
            
            if msg_type == 'ai':
                context += f"[YOU (Atlas)]: {content}\n"
            else:
                context += f"{username}: {content}\n"
        
        context += "\n"
        return context
    
    def _build_task_prompt(self, room_context: Dict, trigger_info: Dict) -> str:
        """Build the current task/situation prompt"""
        
        trigger_type = trigger_info.get('type', 'general')
        trigger_reason = trigger_info.get('reason', '')
        priority = trigger_info.get('priority', 'medium')
        
        num_users = room_context.get('num_users', 0)
        current_topic = room_context.get('current_topic', 'General chat')
        conversation_flow = room_context.get('conversation_flow', 'active')
        group_mood = room_context.get('group_mood', 'neutral')
        
        prompt = f"""🎯 CURRENT SITUATION:

Users: {num_users}
Topic: {current_topic}
Flow: {conversation_flow}
Group Mood: {group_mood}

TRIGGER: {trigger_type} (Priority: {priority})
Reason: {trigger_reason}

YOUR TASK:
"""
        
        # Task based on trigger type
        if trigger_type == 'direct_mention':
            prompt += "User mentioned you directly. Respond to what they said!"
        
        elif trigger_type == 'question':
            prompt += "User asked a question. Answer it clearly and briefly!"
        
        elif trigger_type == 'welcome':
            prompt += "New user just joined! Welcome them and bring them into the conversation!"
        
        elif trigger_type == 'engage':
            prompt += "Someone seems quiet or disengaged. Pull them into the conversation with @tag and engaging question!"
        
        elif trigger_type == 'moderate':
            prompt += "Guide the conversation. Maybe change topic, energize the room, or bridge connections!"
        
        elif trigger_type == 'single_user_engagement':
            prompt += "You're chatting 1-on-1 with someone. Keep them engaged with questions about their interests!"
        
        else:
            prompt += "Keep the conversation flowing. Be a great host!"
        
        prompt += "\n\n"
        prompt += "REMEMBER:\n"
        prompt += "✓ Be BRIEF (15-30 words max)\n"
        prompt += "✓ Use @tags to address specific people\n"
        prompt += "✓ Reference what they said to show you're listening\n"
        prompt += "✓ Ask questions that spark conversation\n"
        prompt += "✓ Match the room's energy\n"
        prompt += "✓ NO 'Atlas:' prefix, NO quotes around response\n\n"
        prompt += "Now respond as the host of this room:"
        
        return prompt
    
    def determine_response_params(self, trigger_info: Dict) -> Dict[str, Any]:
        """Determine max_tokens and temperature based on trigger"""
        
        trigger_type = trigger_info.get('type', 'general')
        priority = trigger_info.get('priority', 'medium')
        
        # Base params - keep responses SHORT
        params = {
            'max_tokens': 100,  # About 15-30 words
            'temperature': 0.7
        }
        
        # Adjust based on trigger
        if trigger_type in ['welcome', 'engage']:
            params['max_tokens'] = 120  # Slightly longer for welcomes
            params['temperature'] = 0.8  # More creative
        
        elif trigger_type in ['question', 'direct_mention']:
            params['max_tokens'] = 100
            params['temperature'] = 0.6  # More focused
        
        elif trigger_type == 'moderate':
            params['max_tokens'] = 110
            params['temperature'] = 0.75
        
        return params


host_prompt_builder = HostPromptBuilder()

