"""
Context Manager - Manages user and room context for AI
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import time

from app.core.redis_client import redis_client
from app.utils.sentiment_analyzer import analyze_sentiment, detect_engagement_level
from app.utils.trigger_detector import TriggerDetector
from app.utils.prompt_builder import AIPromptOrchestrator


class ContextManager:
    """Manages conversation context for AI responses"""
    
    @staticmethod
    async def initialize_user_context(user_id: str, username: str, room_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize user context when joining a room - check for existing session"""
        # Check if user has existing context (session management)
        existing_context = await redis_client.get_user_context(user_id)
        
        if existing_context and existing_context.get("current_room") == room_id:
            # User is rejoining within session expiry (1 hour)
            existing_context["is_new_to_room"] = False
            existing_context["rejoined_at"] = datetime.utcnow().isoformat()
            await redis_client.set_user_context(user_id, existing_context, ttl=3600)
            return existing_context
        
        # Create new context for new user or expired session
        context = {
            "user_id": user_id,
            "name": username,
            "avatar": user_data.get("avatar_style", "human"),
            "avatar_color": user_data.get("avatar_color", "blue"),
            "current_room": room_id,
            "joined_at": datetime.utcnow().isoformat(),
            "is_new_to_room": True,
            "session_id": f"session_{user_id}_{int(datetime.utcnow().timestamp())}",
            
            # Emotional State
            "sentiment": {
                "current": "neutral",
                "history": []
            },
            
            # Participation Metrics
            "participation": {
                "message_count": 0,
                "last_message_time": datetime.utcnow().isoformat(),
                "silence_duration": 0,
                "engagement_score": 0.5,
                "is_active": True
            },
            
            # Conversation Context
            "conversation_history": [],
            
            # Learned Preferences
            "preferences": {
                "topics_discussed": []
            }
        }
        
        # Store with 1 hour TTL (session expiry)
        await redis_client.set_user_context(user_id, context, ttl=3600)
        return context
    
    @staticmethod
    async def update_user_context(user_id: str, message: str, sentiment: Optional[str] = None):
        """Update user context after message"""
        context = await redis_client.get_user_context(user_id)
        
        if not context:
            return
        
        # Analyze sentiment if not provided
        if not sentiment:
            sentiment, _ = analyze_sentiment(message)
        
        # Update participation
        context["participation"]["message_count"] += 1
        context["participation"]["last_message_time"] = datetime.utcnow().isoformat()
        context["participation"]["silence_duration"] = 0
        context["participation"]["is_active"] = True
        
        # Update sentiment
        context["sentiment"]["current"] = sentiment
        context["sentiment"]["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "sentiment": sentiment,
            "trigger": "message_sent"
        })
        
        # Keep only last 10 sentiment records
        context["sentiment"]["history"] = context["sentiment"]["history"][-10:]
        
        # Update conversation history
        context["conversation_history"].append({
            "time": datetime.utcnow().isoformat(),
            "message": message
        })
        
        # Keep only last 20 messages
        context["conversation_history"] = context["conversation_history"][-20:]
        
        # Mark as not new anymore
        context["is_new_to_room"] = False
        
        await redis_client.set_user_context(user_id, context)
    
    @staticmethod
    async def update_silence_duration(user_id: str):
        """Update user's silence duration"""
        context = await redis_client.get_user_context(user_id)
        
        if not context:
            return
        
        last_message = context["participation"]["last_message_time"]
        last_time = datetime.fromisoformat(last_message)
        silence = int((datetime.utcnow() - last_time).total_seconds())
        
        context["participation"]["silence_duration"] = silence
        context["participation"]["is_active"] = silence < 120
        
        await redis_client.set_user_context(user_id, context)
    
    @staticmethod
    async def initialize_room_state(room_id: str, room_type: str, ai_persona: str) -> Dict[str, Any]:
        """Initialize room state"""
        state = {
            "room_id": room_id,
            "room_type": room_type,
            "ai_persona": ai_persona,
            "created_at": datetime.utcnow().isoformat(),
            
            # Active Users
            "users": [],
            
            # Conversation Flow
            "conversation_graph": {
                "current_topic": "general",
                "topic_history": [],
                "threads": []
            },
            
            # Group Dynamics
            "dynamics": {
                "dominant_speaker": None,
                "quiet_users": [],
                "sentiment_average": 0.5,
                "conflict_detected": False,
                "needs_moderation": False
            },
            
            # AI Intervention Queue
            "ai_queue": []
        }
        
        await redis_client.set_room_state(room_id, state)
        return state
    
    @staticmethod
    async def add_user_to_room(room_id: str, user_id: str, username: str):
        """Add user to room state"""
        # CRITICAL: ALWAYS add user to Redis set first
        await redis_client.add_user_to_room(room_id, user_id)
        
        # Then update room state if it exists
        state = await redis_client.get_room_state(room_id)
        
        if not state:
            return
        
        # Add user if not already in list
        user_info = {"id": user_id, "name": username, "status": "active"}
        
        if not any(u["id"] == user_id for u in state["users"]):
            state["users"].append(user_info)
        
        await redis_client.set_room_state(room_id, state)
    
    @staticmethod
    async def remove_user_from_room(room_id: str, user_id: str):
        """Remove user from room state"""
        state = await redis_client.get_room_state(room_id)
        
        if not state:
            return
        
        state["users"] = [u for u in state["users"] if u["id"] != user_id]
        
        await redis_client.set_room_state(room_id, state)
        await redis_client.remove_user_from_room(room_id, user_id)
    
    @staticmethod
    async def build_ai_prompt(room_id: str, trigger: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build AI prompt using intelligent prompt builder
        NEW: Uses conversation memory and advanced context tracking
        """
        try:
            print(f"📝 DEBUG [build_ai_prompt]: Starting for room {room_id}")
            
            from app.services.intelligent_prompt_builder import intelligent_prompt_builder
            print(f"✅ DEBUG: intelligent_prompt_builder imported successfully")
            
            # Get room state
            room_state = await redis_client.get_room_state(room_id)
            print(f"🏠 DEBUG: Room state: {room_state is not None}")
            
            if not room_state:
                # Initialize basic room state if missing
                print(f"⚠️ DEBUG: No room state found, using defaults")
                room_state = {
                    "room_id": room_id,
                    "room_type": "private_room_default",
                    "ai_persona": "Atlas",
                    "users": [],
                    "dynamics": {}
                }
            
            # Get all user contexts
            user_ids = await redis_client.get_room_users(room_id)
            print(f"👥 DEBUG: Found {len(user_ids)} users in room")
            user_states = []
            
            for uid in user_ids:
                context = await redis_client.get_user_context(uid)
                if context:
                    user_states.append(context)
                    print(f"   ✅ User {context.get('name', uid[:8])} context loaded")
            
            print(f"📊 DEBUG: Total user states: {len(user_states)}")
            
            # Use intelligent prompt builder
            room_type = room_state.get("room_type", "private_room_default")
            print(f"🎭 DEBUG: Room type: {room_type}")
            
            print(f"🚀 DEBUG: Calling intelligent_prompt_builder.build_prompt...")
            result = await intelligent_prompt_builder.build_prompt(
                room_id=room_id,
                room_type=room_type,
                trigger=trigger,
                user_states=user_states
            )
            print(f"✅ DEBUG: Prompt built successfully, has {len(result.get('messages', []))} messages")
            
            return result
            
        except Exception as e:
            print(f"❌ DEBUG [build_ai_prompt]: ERROR: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    @staticmethod
    async def detect_triggers(room_id: str, user_id: str, message: str) -> List[Dict[str, Any]]:
        """Detect if AI should respond"""
        triggers = []
        
        # Get contexts
        room_state = await redis_client.get_room_state(room_id)
        user_state = await redis_client.get_user_context(user_id)
        
        if not room_state or not user_state:
            return triggers
        
        # Check for message-based triggers
        trigger = TriggerDetector.detect_trigger(
            message, user_state, room_state, room_state.get("ai_persona", "")
        )
        
        if trigger:
            triggers.append(trigger)
        
        # Check for new user
        if user_state.get("is_new_to_room"):
            new_user_trigger = TriggerDetector.check_new_user(user_state)
            if new_user_trigger:
                triggers.append(new_user_trigger)
        
        return triggers


context_manager = ContextManager()

