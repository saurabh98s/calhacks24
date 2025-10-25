"""
Enhanced Memory Manager - Tracks detailed user context, mood, topics, and conversation flow
This provides rich context for the AI host to be truly conversational and aware
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)


class EnhancedMemoryManager:
    """
    Tracks detailed conversation memory for each user:
    - What they're talking about (topics)
    - Their current mood
    - Their conversation style
    - Key moments in their conversation
    - Questions they've asked
    - Interests they've mentioned
    """
    
    def __init__(self):
        self.redis = redis_client
    
    async def update_user_memory(
        self,
        user_id: str,
        username: str,
        message: str,
        room_id: str
    ) -> Dict[str, Any]:
        """
        Update user's memory with new message
        Tracks topics, mood, interests, questions
        """
        
        try:
            # Get existing memory
            memory = await self.get_user_memory(user_id, room_id)
            
            if not memory:
                memory = self._init_user_memory(user_id, username, room_id)
            
            # Update message history
            memory['messages'].append({
                'content': message,
                'timestamp': datetime.utcnow().isoformat(),
                'room_id': room_id
            })
            
            # Keep only last 20 messages
            memory['messages'] = memory['messages'][-20:]
            
            # Extract and update topics
            topics = self._extract_topics(message)
            for topic in topics:
                if topic not in memory['topics_discussed']:
                    memory['topics_discussed'].append(topic)
            
            # Keep only last 10 topics
            memory['topics_discussed'] = memory['topics_discussed'][-10:]
            
            # Detect mood
            mood = self._detect_mood(message)
            if mood:
                memory['current_mood'] = mood
                memory['mood_history'].append({
                    'mood': mood,
                    'timestamp': datetime.utcnow().isoformat()
                })
                memory['mood_history'] = memory['mood_history'][-10:]
            
            # Track questions
            if '?' in message:
                memory['questions_asked'].append({
                    'question': message,
                    'timestamp': datetime.utcnow().isoformat(),
                    'answered': False
                })
                memory['questions_asked'] = memory['questions_asked'][-5:]
            
            # Detect interests
            interests = self._extract_interests(message)
            for interest in interests:
                if interest not in memory['interests']:
                    memory['interests'].append(interest)
            
            # Update metadata
            memory['message_count'] += 1
            memory['last_active'] = datetime.utcnow().isoformat()
            memory['last_message'] = message
            
            # Save to Redis
            await self._save_user_memory(user_id, room_id, memory)
            
            return memory
            
        except Exception as e:
            logger.error(f"Error updating user memory: {e}")
            return {}
    
    async def get_user_memory(self, user_id: str, room_id: str) -> Optional[Dict[str, Any]]:
        """Get user's detailed memory"""
        try:
            # Ensure Redis is connected
            if self.redis.redis is None:
                await self.redis.connect()
            
            key = f"user_memory:{room_id}:{user_id}"
            data = await self.redis.redis.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user memory: {e}")
            return None
    
    async def get_room_conversation_context(self, room_id: str) -> Dict[str, Any]:
        """
        Get full conversation context for the room
        Returns detailed info about all users and current conversation state
        """
        try:
            # Get all users in room
            user_ids = await self.redis.get_room_users(room_id)
            
            user_memories = []
            for user_id in user_ids:
                memory = await self.get_user_memory(user_id, room_id)
                if memory:
                    user_memories.append(memory)
            
            # Get conversation history
            history = await self.redis.get_conversation_history(room_id, limit=15)
            
            # Analyze current conversation state
            current_topic = self._identify_current_topic(history, user_memories)
            conversation_flow = self._analyze_conversation_flow(history)
            group_mood = self._analyze_group_mood(user_memories)
            
            return {
                'room_id': room_id,
                'num_users': len(user_memories),
                'user_memories': user_memories,
                'recent_messages': history,
                'current_topic': current_topic,
                'conversation_flow': conversation_flow,
                'group_mood': group_mood,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting room context: {e}")
            return {}
    
    async def mark_question_answered(self, user_id: str, room_id: str, question: str):
        """Mark a user's question as answered"""
        memory = await self.get_user_memory(user_id, room_id)
        if memory:
            for q in memory['questions_asked']:
                if q['question'] == question:
                    q['answered'] = True
            await self._save_user_memory(user_id, room_id, memory)
    
    def _init_user_memory(self, user_id: str, username: str, room_id: str) -> Dict[str, Any]:
        """Initialize new user memory"""
        return {
            'user_id': user_id,
            'username': username,
            'room_id': room_id,
            'message_count': 0,
            'messages': [],
            'topics_discussed': [],
            'current_mood': 'neutral',
            'mood_history': [],
            'questions_asked': [],
            'interests': [],
            'conversation_style': 'observing',  # observing, active, talkative, quiet
            'joined_at': datetime.utcnow().isoformat(),
            'last_active': datetime.utcnow().isoformat(),
            'last_message': None
        }
    
    def _extract_topics(self, message: str) -> List[str]:
        """Extract conversation topics from message"""
        topics = []
        message_lower = message.lower()
        
        # Common topic keywords
        topic_keywords = {
            'coding': ['code', 'programming', 'python', 'javascript', 'django', 'react', 'developer'],
            'gaming': ['game', 'gaming', 'play', 'gamer', 'steam', 'xbox', 'playstation'],
            'food': ['food', 'pizza', 'eat', 'restaurant', 'cook', 'recipe', 'hungry'],
            'sports': ['sport', 'football', 'basketball', 'soccer', 'tennis', 'gym', 'workout'],
            'music': ['music', 'song', 'band', 'concert', 'guitar', 'piano', 'spotify'],
            'movies': ['movie', 'film', 'watch', 'netflix', 'cinema', 'actor'],
            'work': ['work', 'job', 'office', 'meeting', 'project', 'deadline'],
            'travel': ['travel', 'trip', 'vacation', 'visit', 'country', 'flight'],
            'tech': ['tech', 'technology', 'ai', 'computer', 'software', 'hardware'],
            'art': ['art', 'draw', 'paint', 'design', 'creative', 'artist']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _detect_mood(self, message: str) -> Optional[str]:
        """Detect mood from message"""
        message_lower = message.lower()
        
        moods = {
            'excited': ['!', 'awesome', 'amazing', 'great', 'love', 'excited', 'yay', 'woohoo'],
            'happy': ['happy', 'good', 'nice', 'cool', 'thanks', 'haha', 'lol'],
            'confused': ['?', 'confused', 'don\'t understand', 'what', 'how', 'help'],
            'frustrated': ['ugh', 'annoying', 'frustrated', 'angry', 'hate', 'tired'],
            'sad': ['sad', 'down', 'depressed', 'lonely', 'miss'],
            'bored': ['bored', 'boring', 'nothing', 'meh'],
            'thoughtful': ['thinking', 'wonder', 'interesting', 'hmm', 'curious']
        }
        
        for mood, indicators in moods.items():
            if any(indicator in message_lower for indicator in indicators):
                return mood
        
        return 'neutral'
    
    def _extract_interests(self, message: str) -> List[str]:
        """Extract user interests from message"""
        interests = []
        message_lower = message.lower()
        
        # Common interest patterns
        interest_patterns = [
            ('i love', 5),
            ('i like', 5),
            ('i enjoy', 5),
            ('i\'m into', 5),
            ('into', 5),
            ('fan of', 5),
            ('interested in', 5)
        ]
        
        for pattern, context_length in interest_patterns:
            if pattern in message_lower:
                # Extract the interest (next few words after pattern)
                start = message_lower.find(pattern) + len(pattern)
                interest = message[start:start+30].strip().split()[0:3]
                if interest:
                    interests.append(' '.join(interest))
        
        return interests
    
    def _identify_current_topic(self, history: List[Dict], user_memories: List[Dict]) -> str:
        """Identify what users are currently talking about"""
        if not history:
            return "No active conversation"
        
        # Get topics from recent messages
        recent_topics = []
        for msg in history[-5:]:
            content = msg.get('message', '')
            topics = self._extract_topics(content)
            recent_topics.extend(topics)
        
        if recent_topics:
            # Most common topic
            topic_counts = {}
            for topic in recent_topics:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
            most_common = max(topic_counts, key=topic_counts.get)
            return most_common
        
        return "General chat"
    
    def _analyze_conversation_flow(self, history: List[Dict]) -> str:
        """Analyze how the conversation is flowing"""
        if not history:
            return "silent"
        
        if len(history) >= 5:
            return "active"
        elif len(history) >= 2:
            return "warming_up"
        else:
            return "just_started"
    
    def _analyze_group_mood(self, user_memories: List[Dict]) -> str:
        """Analyze overall group mood"""
        if not user_memories:
            return "neutral"
        
        moods = [mem.get('current_mood', 'neutral') for mem in user_memories]
        
        # Count positive vs negative
        positive = sum(1 for m in moods if m in ['excited', 'happy'])
        negative = sum(1 for m in moods if m in ['frustrated', 'sad', 'bored'])
        
        if positive > negative:
            return "positive"
        elif negative > positive:
            return "needs_energy"
        else:
            return "neutral"
    
    async def _save_user_memory(self, user_id: str, room_id: str, memory: Dict[str, Any]):
        """Save user memory to Redis"""
        try:
            # Ensure Redis is connected
            if self.redis.redis is None:
                await self.redis.connect()
            
            key = f"user_memory:{room_id}:{user_id}"
            # Use setex to set value with expiry in one operation
            await self.redis.redis.setex(key, 86400, json.dumps(memory))
        except Exception as e:
            logger.error(f"Error saving user memory: {e}")


enhanced_memory_manager = EnhancedMemoryManager()

