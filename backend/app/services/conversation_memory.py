"""
Advanced Conversation Memory System
Tracks individual user conversations with semantic understanding
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
import re

from app.core.redis_client import redis_client


class ConversationMemory:
    """
    Manages conversation memory for each user with semantic tracking
    Maintains conversation threads, topics, and user interaction patterns
    """
    
    def __init__(self):
        self.topic_keywords = {
            'greeting': ['hi', 'hello', 'hey', 'howdy', 'greetings', 'good morning', 'good evening'],
            'question': ['how', 'what', 'when', 'where', 'why', 'who', 'which', 'can', 'could', 'would', 'should'],
            'help': ['help', 'assist', 'support', 'stuck', 'confused', 'don\'t understand', 'explain'],
            'agreement': ['yes', 'yeah', 'sure', 'okay', 'agree', 'right', 'exactly', 'definitely'],
            'disagreement': ['no', 'nope', 'disagree', 'wrong', 'but', 'however', 'actually'],
            'gratitude': ['thank', 'thanks', 'appreciate', 'grateful'],
            'excitement': ['awesome', 'great', 'amazing', 'fantastic', 'cool', 'wow', 'excellent'],
            'concern': ['worried', 'concerned', 'anxious', 'nervous', 'afraid', 'scared'],
        }
    
    async def get_user_conversation_context(self, user_id: str, room_id: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get comprehensive conversation context for a specific user
        Returns: User's message history, topics discussed, interaction patterns
        """
        # Get full conversation history
        full_history = await redis_client.get_conversation_history(room_id, limit=50)
        
        # Extract this user's messages
        user_messages = []
        ai_responses_to_user = []
        other_users_messages = []
        
        for msg in full_history:
            msg_user_id = msg.get('user_id')
            msg_type = msg.get('message_type', 'user')
            
            if msg_user_id == user_id and msg_type == 'user':
                user_messages.append(msg)
            elif msg_type == 'ai':
                # Check if AI was responding to this user
                content = msg.get('message', msg.get('content', '')).lower()
                user_context = await redis_client.get_user_context(user_id)
                username = user_context.get('name', '') if user_context else ''
                
                if username and f"@{username.lower()}" in content:
                    ai_responses_to_user.append(msg)
            else:
                other_users_messages.append(msg)
        
        # Analyze conversation patterns
        topics = self._extract_topics(user_messages)
        questions = self._extract_questions(user_messages)
        interaction_style = self._analyze_interaction_style(user_messages)
        conversation_thread = self._build_conversation_thread(user_id, full_history[-limit:])
        
        return {
            'user_messages': user_messages[-limit:],
            'ai_responses': ai_responses_to_user[-5:],
            'topics_discussed': topics,
            'questions_asked': questions,
            'interaction_style': interaction_style,
            'conversation_thread': conversation_thread,
            'last_message_time': user_messages[-1].get('timestamp') if user_messages else None,
            'message_count': len(user_messages),
            'engagement_level': self._calculate_engagement(user_messages)
        }
    
    async def get_room_conversation_state(self, room_id: str) -> Dict[str, Any]:
        """
        Get comprehensive state of the room conversation
        Returns: Current topic, active threads, conversation momentum
        """
        history = await redis_client.get_conversation_history(room_id, limit=20)
        
        if not history:
            return {
                'current_topic': None,
                'conversation_momentum': 'cold',
                'active_threads': [],
                'recent_speakers': [],
                'needs_intervention': True
            }
        
        # Analyze recent conversation
        recent_messages = history[:10]  # Most recent 10
        
        # Extract current topic
        current_topic = self._identify_current_topic(recent_messages)
        
        # Identify active conversation threads
        threads = self._identify_conversation_threads(recent_messages)
        
        # Calculate conversation momentum
        momentum = self._calculate_momentum(recent_messages)
        
        # Get recent speakers
        recent_speakers = list(dict.fromkeys([
            msg.get('username', 'Unknown') 
            for msg in recent_messages 
            if msg.get('message_type') == 'user'
        ]))
        
        # Determine if AI intervention needed
        needs_intervention = self._needs_intervention(recent_messages)
        
        return {
            'current_topic': current_topic,
            'conversation_momentum': momentum,
            'active_threads': threads,
            'recent_speakers': recent_speakers[:5],
            'needs_intervention': needs_intervention,
            'last_message_time': recent_messages[0].get('timestamp') if recent_messages else None
        }
    
    def _extract_topics(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract topics from user messages"""
        topics = []
        for msg in messages:
            content = msg.get('message', msg.get('content', '')).lower()
            for topic, keywords in self.topic_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if topic not in topics:
                        topics.append(topic)
        return topics
    
    def _extract_questions(self, messages: List[Dict[str, Any]]) -> List[str]:
        """Extract actual questions asked by user"""
        questions = []
        for msg in messages[-5:]:  # Last 5 messages
            content = msg.get('message', msg.get('content', ''))
            if '?' in content:
                questions.append(content.strip())
        return questions
    
    def _analyze_interaction_style(self, messages: List[Dict[str, Any]]) -> str:
        """Determine user's interaction style"""
        if not messages:
            return 'new'
        
        total_words = sum(len(msg.get('message', '').split()) for msg in messages)
        avg_words = total_words / len(messages) if messages else 0
        
        has_questions = any('?' in msg.get('message', '') for msg in messages)
        
        if avg_words > 20:
            return 'verbose'
        elif has_questions and len(messages) > 3:
            return 'inquisitive'
        elif len(messages) < 3:
            return 'quiet'
        else:
            return 'conversational'
    
    def _build_conversation_thread(self, user_id: str, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build conversation thread showing user's interactions with others"""
        thread = []
        
        for i, msg in enumerate(history):
            msg_user_id = msg.get('user_id')
            msg_type = msg.get('message_type', 'user')
            
            # Add user's messages and immediate responses
            if msg_user_id == user_id or (i > 0 and history[i-1].get('user_id') == user_id):
                thread.append({
                    'speaker': msg.get('username', 'Unknown'),
                    'message': msg.get('message', msg.get('content', '')),
                    'type': msg_type,
                    'timestamp': msg.get('timestamp')
                })
        
        return thread[-10:]  # Last 10 interactions
    
    def _calculate_engagement(self, messages: List[Dict[str, Any]]) -> str:
        """Calculate user engagement level"""
        if not messages:
            return 'none'
        
        count = len(messages)
        
        # Check recency
        if messages:
            last_msg_time = messages[-1].get('timestamp')
            if last_msg_time:
                try:
                    # Handle ISO format timestamp
                    if isinstance(last_msg_time, str):
                        last_time_str = last_msg_time.replace('Z', '+00:00')
                        last_time = datetime.fromisoformat(last_time_str)
                        time_diff = (datetime.utcnow() - last_time.replace(tzinfo=None)).total_seconds()
                        
                        if time_diff > 300:  # 5 minutes
                            return 'dropped_off'
                except Exception as e:
                    # If timestamp parsing fails, continue without recency check
                    pass
        
        if count >= 10:
            return 'very_high'
        elif count >= 5:
            return 'high'
        elif count >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _identify_current_topic(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Identify current conversation topic"""
        if not messages:
            return None
        
        # Look at last 5 messages to determine topic
        recent_content = ' '.join([
            msg.get('message', msg.get('content', '')).lower() 
            for msg in messages[:5]
        ])
        
        # Check for common topics
        topic_scores = {}
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword in recent_content)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        # Try to extract key nouns (simple approach)
        words = recent_content.split()
        if words:
            # Return a snippet of the conversation
            return ' '.join(messages[0].get('message', '').split()[:5]) + '...'
        
        return 'general_conversation'
    
    def _identify_conversation_threads(self, messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Identify active conversation threads between users"""
        threads = []
        
        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]
            
            current_user = current.get('username', 'Unknown')
            next_user = next_msg.get('username', 'Unknown')
            current_type = current.get('message_type', 'user')
            next_type = next_msg.get('message_type', 'user')
            
            # Detect user-to-user conversations
            if current_type == 'user' and next_type == 'user' and current_user != next_user:
                threads.append({
                    'participants': [current_user, next_user],
                    'last_message': next_msg.get('message', '')[:50]
                })
            
            # Detect @mentions
            content = current.get('message', current.get('content', ''))
            mentions = re.findall(r'@(\w+)', content)
            if mentions:
                threads.append({
                    'participants': [current_user] + mentions,
                    'type': 'mention',
                    'last_message': content[:50]
                })
        
        return threads[-3:]  # Last 3 threads
    
    def _calculate_momentum(self, messages: List[Dict[str, Any]]) -> str:
        """Calculate conversation momentum"""
        if not messages:
            return 'cold'
        
        user_messages = [m for m in messages if m.get('message_type') == 'user']
        
        if not user_messages:
            return 'cold'
        
        # Check timing between messages
        try:
            if len(user_messages) >= 2:
                latest_ts = user_messages[0].get('timestamp', '')
                previous_ts = user_messages[1].get('timestamp', '')
                
                if latest_ts and previous_ts:
                    latest = datetime.fromisoformat(latest_ts.replace('Z', '+00:00'))
                    previous = datetime.fromisoformat(previous_ts.replace('Z', '+00:00'))
                    gap = abs((latest - previous).total_seconds())
                    
                    if gap < 30:
                        return 'hot'
                    elif gap < 120:
                        return 'warm'
                    else:
                        return 'cooling'
        except Exception as e:
            # If timestamp parsing fails, continue with message count check
            pass
        
        # Check message frequency
        if len(user_messages) >= 5:
            return 'warm'
        elif len(user_messages) >= 2:
            return 'moderate'
        else:
            return 'cold'
    
    def _needs_intervention(self, messages: List[Dict[str, Any]]) -> bool:
        """Determine if AI intervention is needed"""
        if not messages:
            return True
        
        recent_user_msgs = [m for m in messages[:5] if m.get('message_type') == 'user']
        recent_ai_msgs = [m for m in messages[:5] if m.get('message_type') == 'ai']
        
        # Too many AI messages
        if len(recent_ai_msgs) > len(recent_user_msgs):
            return False
        
        # No recent messages
        if not recent_user_msgs:
            return True
        
        # Check for questions
        has_unanswered_questions = any('?' in m.get('message', '') for m in recent_user_msgs[:2])
        if has_unanswered_questions and not recent_ai_msgs:
            return True
        
        # Check for @AI mentions
        for msg in recent_user_msgs[:2]:
            content = msg.get('message', '').lower()
            if '@atlas' in content or '@ai' in content:
                return True
        
        return False


conversation_memory = ConversationMemory()

