"""
WebSocket handler using Socket.IO
"""
import socketio
import logging
import asyncio
from datetime import datetime, timedelta
from uuid import UUID
from typing import Set

from app.core.redis_client import redis_client
from app.services.context_manager import context_manager
from app.services.ai_service import ai_service
from app.services.user_service import user_service
from app.services.room_service import room_service
from app.services.multiagent_service import get_multiagent_service
from app.core.database import AsyncSessionLocal
from app.utils.sentiment_analyzer import analyze_sentiment
from app.services.trigger_ai_service import trigger_ai_service
from app.services.enhanced_memory_manager import enhanced_memory_manager
from app.services.host_prompt_builder import host_prompt_builder

logger = logging.getLogger(__name__)

# Track rooms being monitored for silence
monitored_rooms: Set[str] = set()

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    logger=True,
    engineio_logger=False
)


@sio.event
async def connect(sid, environ, auth):
    """Handle client connection"""
    logger.info(f"🔌 Client connected: {sid}")
    
    # Store auth data in session
    if auth and "token" in auth:
        await sio.save_session(sid, {"token": auth["token"]})
    
    return True


@sio.event
async def disconnect(sid):
    """Handle client disconnection with cleanup"""
    logger.info(f"👋 Client disconnected: {sid}")
    
    # Get session data
    session = await sio.get_session(sid)
    
    if "room_id" in session and "user_id" in session:
        room_id = session["room_id"]
        user_id = session["user_id"]
        
        # Remove user from room
        await context_manager.remove_user_from_room(room_id, user_id)
        
        # Notify room
        await sio.emit("user_left", {
            "user_id": user_id,
            "username": session.get("username", "User"),
            "timestamp": datetime.utcnow().isoformat()
        }, room=room_id)
        
        # Leave Socket.IO room
        sio.leave_room(sid, room_id)
        
        # Update active users count and check if room is empty
        users = await redis_client.get_room_users(room_id)
        async with AsyncSessionLocal() as db:
            room = await room_service.get_room_by_room_id(db, room_id)
            if room:
                await room_service.update_active_users(db, room.id, len(users))
            
            # Clean up guest user from database
            try:
                from app.services.user_service import user_service
                await user_service.delete_guest_user(db, UUID(user_id))
                logger.info(f"🗑️ Deleted guest user {user_id} from database")
            except Exception as e:
                logger.error(f"❌ Failed to delete guest user: {e}")
            
            # If room is now empty, delete it
            if len(users) == 0 and room:
                logger.info(f"🗑️ Room {room_id} is empty - deleting room and cleaning up data")
                
                # Delete room from database
                await room_service.delete_room(db, room.id)
                
                # Clean up Redis data
                await redis_client.delete_room_state(room_id)
                await redis_client.delete_conversation_history(room_id)
                
                # Stop monitoring
                stop_room_monitoring(room_id)
                
                logger.info(f"✅ Room {room_id} deleted successfully")


@sio.event
async def join_room(sid, data):
    """Handle user joining a room"""
    logger.info(f"========== JOIN_ROOM CALLED ==========")
    logger.info(f"SID: {sid}, DATA: {data}")
    
    try:
        room_id = data.get("room_id")
        user_id = data.get("user_id")
        username = data.get("username")
        
        logger.info(f"👤 User {username} joining room {room_id}")
        
        # Save session FIRST
        await sio.save_session(sid, {
            "room_id": room_id,
            "user_id": user_id,
            "username": username,
            **data
        })
        
        # Join Socket.IO room - USE ONLY ONE METHOD
        await sio.enter_room(sid, room_id)
        
        # Verify socket is in room (for debugging)
        rooms_for_sid = sio.manager.get_rooms(sid, '/')
        logger.info(f"🔍 Socket {sid} is now in rooms: {list(rooms_for_sid)}")
        
        # Use a single DB session for the entire operation
        async with AsyncSessionLocal() as db:
            # Get user data from DB
            user = await user_service.get_user_by_id(db, UUID(user_id))
            
            if not user:
                await sio.emit("error", {"message": "User not found"}, to=sid)
                return
            
            # Initialize user context
            user_data = {
                "avatar_style": user.avatar_style,
                "avatar_color": user.avatar_color,
                "mood_icon": user.mood_icon
            }
            
            await context_manager.initialize_user_context(user_id, username, room_id, user_data)
            
            # Add user to room in Redis
            await context_manager.add_user_to_room(room_id, user_id, username)
            
            # VERIFY: Check that the joining user was added to Redis
            users = await redis_client.get_room_users(room_id)
            print(f"🔍 DEBUG: Redis returned {len(users)} users for room {room_id}: {users}")
            logger.info(f"🔍 Redis returned {len(users)} users for room {room_id}: {users}")
            
            if user_id not in users:
                logger.error(f"❌ CRITICAL: User {user_id} ({username}) was NOT added to Redis room {room_id}!")
                logger.error(f"   Users in Redis: {users}")
                # Try adding again
                await context_manager.add_user_to_room(room_id, user_id, username)
                users = await redis_client.get_room_users(room_id)
                logger.info(f"   After retry: {users}")
            else:
                logger.info(f"✅ Verified user {user_id} ({username}) is in Redis room users")
            
            # Update room active users count
            room = await room_service.get_room_by_room_id(db, room_id)
            if room:
                await room_service.update_active_users(db, room.id, len(users))
            
            # Get conversation history
            history = await redis_client.get_conversation_history(room_id, limit=50)
            
            # Build active users with full metadata
            # CRITICAL: Filter out ghost users (users in Redis but not in DB)
            active_users_with_metadata = []
            valid_user_ids = []
            
            print(f"📊 DEBUG: Building metadata for {len(users)} users in room {room_id}")
            logger.info(f"📊 Building metadata for {len(users)} users in room {room_id}")
            
            for uid in users:
                logger.info(f"  🔍 Looking up user {uid}")
                user_obj = await user_service.get_user_by_id(db, UUID(uid))
                if user_obj:
                    user_metadata = {
                        "user_id": uid,
                        "username": user_obj.username,
                        "avatar_style": user_obj.avatar_style,
                        "avatar_color": user_obj.avatar_color,
                        "mood_icon": user_obj.mood_icon
                    }
                    active_users_with_metadata.append(user_metadata)
                    valid_user_ids.append(uid)
                    logger.info(f"  ✅ Added metadata for {user_obj.username}: {user_metadata}")
                else:
                    logger.warning(f"  ⚠️ GHOST USER {uid} not found in database - removing from Redis!")
                    # Remove ghost user from Redis
                    await redis_client.remove_user_from_room(room_id, uid)
        
        # CRITICAL: Ensure the joining user is ALWAYS in the response
        if user_id not in valid_user_ids:
            logger.warning(f"⚠️ Joining user {user_id} ({username}) not in valid_user_ids! Adding now.")
            valid_user_ids.append(user_id)
            # Also add their metadata
            active_users_with_metadata.append({
                "user_id": user_id,
                "username": username,
                "avatar_style": user_data["avatar_style"],
                "avatar_color": user_data["avatar_color"],
                "mood_icon": user_data.get("mood_icon", "😊")
            })
        
        print(f"📤 DEBUG: Sending room_joined to {username}")
        print(f"   - valid_user_ids ({len(valid_user_ids)}): {valid_user_ids}")
        print(f"   - active_users_metadata ({len(active_users_with_metadata)}): {active_users_with_metadata}")
        logger.info(f"📤 Sending room_joined to {username} with {len(valid_user_ids)} user IDs and {len(active_users_with_metadata)} metadata entries")
        
        # Send room data to user BEFORE notifying others
        # Use valid_user_ids (ghost users removed)
        room_joined_data = {
            "room_id": room_id,
            "message": "Successfully joined room",
            "conversation_history": history[::-1],  # Reverse to chronological order
            "active_users": valid_user_ids,  # Only valid user IDs (ghost users removed)
            "active_users_metadata": active_users_with_metadata  # Full user data
        }
        
        print(f"")
        print(f"🚀 FINAL DATA TO EMIT:")
        print(f"   Room ID: {room_joined_data['room_id']}")
        print(f"   Active Users Count: {len(room_joined_data['active_users'])}")
        print(f"   Active Users: {room_joined_data['active_users']}")
        print(f"   Metadata Count: {len(room_joined_data['active_users_metadata'])}")
        print(f"   History Count: {len(room_joined_data['conversation_history'])}")
        print(f"")
        
        await sio.emit("room_joined", room_joined_data, to=sid)
        logger.info(f"✅ Emitted room_joined event to {sid}")
        
        # Small delay to ensure client is ready
        await asyncio.sleep(0.1)
        
        # THEN notify room about new user (send full metadata)
        await sio.emit("user_joined", {
            "user_id": user_id,
            "username": username,
            "avatar_style": user_data["avatar_style"],
            "avatar_color": user_data["avatar_color"],
            "mood_icon": user_data.get("mood_icon", "😊"),
            "timestamp": datetime.utcnow().isoformat()
        }, room=room_id)
        
        # Start room monitoring if this is the first user or not already monitored
        start_room_monitoring(room_id)
        
        # Check for new user trigger
        triggers = await context_manager.detect_triggers(room_id, user_id, "")
        
        for trigger in triggers:
            if trigger.get("type") == "new_user_joined":
                # Generate AI welcome (non-blocking)
                asyncio.create_task(generate_ai_response(room_id, trigger))
        
        logger.info(f"✅ User {username} successfully joined room {room_id}")
        
    except Exception as e:
        logger.error(f"❌ ERROR IN JOIN_ROOM: {e}", exc_info=True)
        await sio.emit("error", {"message": str(e)}, to=sid)


@sio.event
async def send_message(sid, data):
    """Handle user message"""
    logger.info(f"========== SEND_MESSAGE CALLED ==========")
    logger.info(f"SID: {sid}, DATA: {data}")
    
    try:
        room_id = data.get("room_id")
        user_id = data.get("user_id")
        username = data.get("username")
        message = data.get("message")
        
        if not all([room_id, user_id, username, message]):
            await sio.emit("error", {"message": "Missing required fields"}, to=sid)
            return
        
        logger.info(f"📨 Message from {username} in room {room_id}: {message}")
        
        # Analyze sentiment
        sentiment, score = analyze_sentiment(message)
        
        # Update user context
        await context_manager.update_user_context(user_id, message, sentiment)
        
        # Get user persona for message (fetch user first to get persona)
        user_persona = None
        async with AsyncSessionLocal() as db:
            temp_user = await user_service.get_user_by_id(db, UUID(user_id))
            if temp_user:
                user_persona = getattr(temp_user, 'persona', None)
        
        # Create message object
        message_obj = {
            "message_id": f"msg_{user_id}_{int(datetime.utcnow().timestamp() * 1000)}",
            "room_id": room_id,
            "user_id": user_id,
            "username": username,
            "message": message,
            "content": message,
            "message_type": "user",
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat(),
            "persona": user_persona  # Include user persona from LinkedIn
        }
        
        # 🚀 MULTI-AGENT MODERATION SYSTEM
        logger.info(f"🎯 Processing message through multi-agent system for room {room_id}")

        # Get room details for multi-agent processing
        async with AsyncSessionLocal() as db:
            user_db = await user_service.get_user_by_id(db, UUID(user_id))
            room_db = await room_service.get_room_by_room_id(db, room_id)

            if not user_db or not room_db:
                logger.error(f"❌ User or room not found for multi-agent processing")
                await sio.emit("error", {"message": "Processing error"}, to=sid)
                return

        # Get user context for multi-agent system
        user_context_data = await redis_client.get_user_context(user_id)

        # Process with multi-agent system if enabled
        from app.config import settings
        if settings.USE_MULTIAGENT:
            multiagent = get_multiagent_service()
            result = await multiagent.process_message(
                message_id=message_obj['message_id'],
                user_id=user_id,
                room_id=room_id,
                message_content=message,
                room_type=room_db.room_type,
                user_context=user_context_data
            )
        else:
            # Intelligent intervention logic when multi-agent is disabled
            logger.info("⚡ Multi-agent disabled - using AI-powered intervention logic")
            
            # Get recent conversation history for context
            history = await redis_client.get_conversation_history(room_id, limit=15)
            
            # Build context for AI decision
            recent_conversation = []
            messages_since_ai = 0
            for hist_msg in reversed(history[-10:]):
                role = "AI" if hist_msg.get("message_type") == "ai" else hist_msg.get("username", "User")
                content = hist_msg.get("message", "")
                if content:
                    recent_conversation.append(f"{role}: {content}")
                if hist_msg.get("message_type") == "ai":
                    break
                if hist_msg.get("message_type") == "user":
                    messages_since_ai += 1
            
            # Check for direct mentions (always respond)
            ai_mentions = ['@atlas', '@ai', 'atlas', 'hey atlas', 'hi atlas']
            message_lower = message.lower()
            is_mentioned = any(mention in message_lower for mention in ai_mentions)
            
            should_respond = False
            response_reason = ""
            
            if is_mentioned:
                # Always respond when mentioned
                should_respond = True
                response_reason = "mentioned"
            else:
                # Use AI to decide if it should participate with FULL ROOM CONTEXT
                conversation_context = "\n".join(recent_conversation[-5:]) if recent_conversation else "No recent messages"
                
                # Get room context description
                from app.services.room_context_builder import get_room_ai_context
                room_context_desc = get_room_ai_context(room_db.room_type, room_db.ai_persona)
                
                # Extract just the role/context summary (first 200 chars)
                room_summary = room_context_desc.split('\n\n')[0] if room_context_desc else f"You are {room_db.ai_persona} in a {room_db.room_type} room."
                
                decision_prompt = f"""ROOM CONTEXT:
{room_summary}

RECENT CONVERSATION:
{conversation_context}

LATEST MESSAGE from {username}: {message}

DECISION CRITERIA:
- You are {room_db.ai_persona} in a {room_db.room_type.upper()} room
- Should you respond based on your role and the room's purpose?
- Does this message need your expertise or facilitation?
- Have you been quiet too long? (last spoke {messages_since_ai} messages ago)
- Would staying silent be better for the group dynamic?

Respond ONLY with: YES or NO
If YES, add reason after pipe |

Format: YES|reason or NO"""

                # Quick AI decision
                decision_messages = [{"role": "user", "content": decision_prompt}]
                decision_response = await ai_service.generate_response(decision_messages, max_tokens=50, temperature=0.3)
                
                if decision_response:
                    decision_text = decision_response.get("content", "").strip().upper()
                    if decision_text.startswith("YES"):
                        should_respond = True
                        # Extract reason if provided
                        if "|" in decision_text:
                            response_reason = decision_text.split("|", 1)[1].strip()
                        else:
                            response_reason = "ai_decision"
                    else:
                        should_respond = False
                        response_reason = "ai_decided_not_to"
                else:
                    # Fallback: respond every 3-4 messages
                    if messages_since_ai >= 3:
                        should_respond = True
                        response_reason = "conversation_flow"
            
            result = {
                "action": "allow",
                "should_intervene": should_respond,
                "ai_response": "",  # Will be generated later if needed
                "metadata": {
                    "multiagent_disabled": True,
                    "intervention_reason": response_reason,
                    "messages_since_ai": messages_since_ai,
                    "is_mentioned": is_mentioned,
                    "intelligent_decision": True
                }
            }
            
            logger.info(f"🧠 AI decision: {should_respond} (reason: {response_reason}, messages_since_ai: {messages_since_ai})")

        # Extract results from multi-agent system
        action = result["action"]
        should_intervene = result["should_intervene"]
        ai_response = result["ai_response"]
        metadata = result["metadata"]

        logger.info(f"🎛️ Multi-agent decision: action={action}, intervene={should_intervene}")

        # Handle moderation actions based on priority system
        if action == "ban":
            logger.critical(f"🚫 BAN ACTION - User {user_id} banned for severe violation")
            await sio.emit("user_banned", {
                "user_id": user_id,
                "reason": metadata.get("toxicity", {}).get("explanation", "Severe policy violation"),
                "severity": "critical"
            }, room=room_id)
            return

        elif action == "mute":
            logger.warning(f"🔇 MUTE ACTION - User {user_id} muted")
            await sio.emit("user_muted", {
                "user_id": user_id,
                "duration": metadata.get("mute_duration", 300),
                "reason": metadata.get("toxicity", {}).get("explanation", "Policy violation")
            }, room=room_id)
            # Don't broadcast the message if muted
            return

        elif action == "warn":
            logger.info(f"⚠️ WARNING - User {user_id} warned")
            await sio.emit("moderation_warning", {
                "message": metadata.get("warning_message", "Please keep messages respectful"),
                "severity": metadata.get("severity", "medium")
            }, room=sid)

        elif action == "alert":
            logger.critical(f"🚨 CRISIS ALERT - User {user_id} in room {room_id}")
            # Log for admin review
            logger.critical(f"CRISIS DETAILS: {metadata}")
            # Send crisis resources to user
            await sio.emit("crisis_resources", {
                "message": "If you're in crisis, please reach out for help:",
                "resources": [
                    "988 Suicide & Crisis Lifeline (call or text)",
                    "Crisis Text Line: Text HOME to 741741",
                    "Emergency Services: 911"
                ]
            }, room=sid)

        # Add to conversation history (only if not banned/muted)
        await redis_client.add_message_to_history(room_id, message_obj)

        # Increment message counts
        async with AsyncSessionLocal() as db:
            if user_db:
                await user_service.increment_message_count(db, UUID(user_id))

            if room_db:
                await room_service.increment_message_count(db, room_db.id)

        # Update enhanced memory
        await enhanced_memory_manager.update_user_memory(user_id, username, message, room_id)

        # BROADCAST user message with emotion indicators
        emotion_data = metadata.get("emotion", {})
        toxicity_data = metadata.get("toxicity", {})

        broadcast_message = {
            **message_obj,
            "emotion": emotion_data.get("emotion"),
            "emotion_score": emotion_data.get("score"),
            "toxicity_score": toxicity_data.get("score")
        }

        await sio.emit("new_message", broadcast_message, room=room_id)
        logger.info(f"✅ User message broadcast complete for room {room_id}")

        # Generate AI response if needed
        if should_intervene:
            logger.info(f"🤖 AI intervention required - generating response")
            
            # If ai_response is empty, generate it now
            if not ai_response:
                logger.info(f"💬 Generating AI response using AI service...")
                
                # Build context from recent messages
                history = await redis_client.get_conversation_history(room_id, limit=10)
                
                # Build conversation context string with personas
                conversation_context = []
                for hist_msg in reversed(history[-8:]):  # Last 8 messages for context
                    role = "You (AI)" if hist_msg.get("message_type") == "ai" else hist_msg.get("username", "User")
                    content = hist_msg.get("message", "")
                    persona = hist_msg.get("persona", "")
                    
                    if content:
                        # Include persona if available
                        if persona and hist_msg.get("message_type") == "user":
                            conversation_context.append(f"{role} [{persona}]: {content}")
                        else:
                            conversation_context.append(f"{role}: {content}")
                
                # Add current message with persona
                if user_persona:
                    conversation_context.append(f"{username} [{user_persona}]: {message}")
                else:
                    conversation_context.append(f"{username}: {message}")
                conversation_text = "\n".join(conversation_context)
                
                # Get room-specific system prompt with detailed context
                from app.services.room_context_builder import get_room_system_prompt
                system_msg = get_room_system_prompt(
                    room_type=room_db.room_type,
                    ai_persona=room_db.ai_persona,
                    conversation_context=conversation_text
                )
                
                # Build messages for AI - include system message properly
                messages = [{"role": "system", "content": system_msg}]
                
                # Generate response with room-appropriate parameters
                # D&D needs more creativity and length for narration
                # Therapy needs balanced, measured responses
                # AA needs warmth and empathy
                room_params = {
                    "dnd": {"temperature": 0.9, "max_tokens": 500},
                    "alcoholics_anonymous": {"temperature": 0.7, "max_tokens": 350},
                    "group_therapy": {"temperature": 0.7, "max_tokens": 350},
                }
                params = room_params.get(room_db.room_type, {"temperature": 0.7, "max_tokens": 300})
                temperature = params["temperature"]
                max_tokens = params["max_tokens"]
                
                response = await ai_service.generate_response(messages, max_tokens=max_tokens, temperature=temperature)
                if response:
                    ai_response = response.get("content", "")
                else:
                    # Fallback responses based on room type
                    fallbacks = {
                        "dnd": "The ancient halls echo with anticipation. What do you do next?",
                        "alcoholics_anonymous": "Thank you for sharing. We're here to support each other, one day at a time.",
                        "group_therapy": "I appreciate you opening up. How does everyone else feel about what was just shared?"
                    }
                    ai_response = fallbacks.get(room_db.room_type, "I'm here and listening. Please continue.")

            # Create AI message
            ai_message = {
                "message_id": f"ai_msg_{int(datetime.utcnow().timestamp() * 1000)}",
                "room_id": room_id,
                "user_id": None,
                "username": room_db.ai_persona,  # Use room's AI persona
                "message": ai_response,
                "content": ai_response,
                "message_type": "ai",
                "ai_persona": room_db.ai_persona,
                "ai_trigger": metadata.get("intervention_reason", action),
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata  # Include full multi-agent metadata
            }

            # Add AI message to history
            await redis_client.add_message_to_history(room_id, ai_message)

            # Broadcast AI response
            await sio.emit("new_message", ai_message, room=room_id)
            logger.info(f"✅ AI response broadcast complete for room {room_id}")

            # Update AI memory
            await enhanced_memory_manager.update_user_memory(
                "atlas_ai",
                room_db.ai_persona,
                ai_response,
                room_id
            )
        
    except Exception as e:
        logger.error(f"❌ ERROR IN SEND_MESSAGE: {e}", exc_info=True)
        await sio.emit("error", {"message": str(e)}, to=sid)


@sio.event
async def typing(sid, data):
    """Handle typing indicator"""
    room_id = data.get("room_id")
    username = data.get("username")
    is_typing = data.get("is_typing", True)
    
    await sio.emit("user_typing", {
        "username": username,
        "is_typing": is_typing
    }, room=room_id, skip_sid=sid)


@sio.event
async def move_avatar(sid, data):
    """Handle avatar movement"""
    room_id = data.get("room_id")
    user_id = data.get("user_id")
    position = data.get("position")
    
    # Broadcast position update
    await sio.emit("avatar_moved", {
        "user_id": user_id,
        "position": position
    }, room=room_id, skip_sid=sid)


async def generate_host_response(room_id: str, room_context: dict, trigger_decision: dict):
    """
    Generate host AI response using the new two-tier system:
    1. Trigger AI (Janitor) decided we should respond
    2. Host Prompt Builder creates rich context
    3. Anthropic Claude generates the actual response
    """
    try:
        logger.info(f"🎤 Generating host response for room {room_id}")

        # 1. Build host prompt with full context
        messages = host_prompt_builder.build_host_prompt(room_context, trigger_decision)

        # 2. Determine response parameters
        params = host_prompt_builder.determine_response_params(trigger_decision)
        max_tokens = params['max_tokens']
        temperature = params['temperature']

        # 3. Generate response using AI
        response = await ai_service.generate_response(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        if not response:
            logger.warning(f"No host response generated for room {room_id}")
            return
        
        # 4. Extract and clean content
        ai_content = response.get("content", "").strip()

        # CRITICAL: Strip any "Atlas:" or persona prefix
        import re
        ai_content = re.sub(r'^(Atlas|atlas|ATLAS):\s*["\']?', '', ai_content, flags=re.IGNORECASE)
        ai_content = re.sub(r'^["\']', '', ai_content)  # Remove leading quotes
        ai_content = re.sub(r'["\']$', '', ai_content)  # Remove trailing quotes
        ai_content = ai_content.strip()

        # CRITICAL: Filter out any SQL queries or system logs that AI might have generated
        if _is_system_message(ai_content):
            logger.warning(f"Host AI generated system message content for room {room_id}")
            return

        # CRITICAL: Don't send empty messages
        if not ai_content or len(ai_content) == 0:
            logger.warning(f"Host returned empty content for room {room_id}")
            return

        # 5. Create AI message
        ai_message = {
            "message_id": f"host_msg_{int(datetime.utcnow().timestamp() * 1000)}",
            "room_id": room_id,
            "user_id": None,
            "username": "Atlas",
            "message": ai_content,
            "content": ai_content,
            "message_type": "ai",
            "ai_persona": "Atlas",
            "ai_trigger": trigger_decision.get("type"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 6. Add to conversation history
        await redis_client.add_message_to_history(room_id, ai_message)

        # 7. Update enhanced memory (AI's own memory)
        await enhanced_memory_manager.update_user_memory(
            "atlas_ai",
            "Atlas",
            ai_content,
            room_id
        )

        # 8. Broadcast to ALL users in room
        logger.info(f"🎤 Broadcasting host message to room {room_id}")
        await sio.emit("new_message", ai_message, room=room_id)

        logger.info(f"✅ Host response sent to room {room_id}")

    except Exception as e:
        logger.error(f"❌ Error generating host response: {e}", exc_info=True)


def _is_system_message(content: str) -> bool:
    """
    Check if a message contains SQL queries, system logs, or debug information
    Prevents SQL logs and system messages from being stored in conversation history
    """
    if not content or not content.strip():
        return True

    content_str = str(content).upper()

    # SQL query patterns
    sql_patterns = [
        'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'FROM ', 'WHERE ',
        'sqlalchemy.engine', 'Engine.', 'BEGIN (implicit)', 'COMMIT',
        'UPDATE users SET', 'UPDATE rooms SET', 'SELECT users.',
        'SELECT rooms.', 'WHERE users.id =', 'WHERE rooms.id =',
        '::UUID', '::VARCHAR', '::INTEGER'
    ]

    # Debug/log patterns
    debug_patterns = [
        'DEBUG', 'INFO', 'WARNING', 'ERROR', 'sqlalchemy.',
        'Engine[', 'cached since', 'emitting event',
        '🔍', '📊', '✅', '❌', '⚠️', '🎯', '🤖', '📝',
        'PRINT(', 'LOGGER.', 'LOG.'
    ]

    # Check if this looks like a SQL query or system log
    is_sql_or_debug = any(
        pattern.upper() in content_str
        for pattern in sql_patterns + debug_patterns
    )

    return is_sql_or_debug


async def generate_ai_response(room_id: str, trigger: dict):
    """Generate AI response based on trigger - optimized for multi-user context"""
    try:
        logger.info(f"🤖 Generating AI response for room {room_id}, trigger: {trigger.get('type')}")

        # Build prompt with full multi-user context
        try:
            prompt_data = await context_manager.build_ai_prompt(room_id, trigger)
        except Exception as e:
            logger.error(f"❌ ERROR building prompt: {e}", exc_info=True)
            return

        if not prompt_data:
            logger.warning(f"No prompt data for room {room_id}")
            return

        if not prompt_data.get("messages"):
            logger.warning(f"No messages in prompt data for room {room_id}")
            return

        # Generate AI response
        response = await ai_service.generate_response(
            messages=prompt_data.get("messages", []),
            max_tokens=prompt_data.get("max_tokens", 500),
            temperature=prompt_data.get("temperature", 0.8)
        )

        if not response:
            logger.warning(f"No AI response generated for room {room_id}")
            return
        
        # Extract content
        ai_content = response.get("content", "").strip()

        # CRITICAL: Strip any "Atlas:" or "Name:" prefix that AI might add
        # AI sometimes includes the persona name in the response
        import re
        ai_content = re.sub(r'^(Atlas|atlas|ATLAS):\s*["\']?', '', ai_content, flags=re.IGNORECASE)
        ai_content = re.sub(r'^["\']', '', ai_content)  # Remove leading quotes
        ai_content = ai_content.strip()

        # CRITICAL: Filter out any SQL queries or system logs that AI might have generated
        if _is_system_message(ai_content):
            logger.warning(f"AI generated system message content for room {room_id}")
            return

        # CRITICAL: Don't send empty messages
        if not ai_content or len(ai_content) == 0:
            logger.warning(f"AI returned empty content for room {room_id}")
            return

        # Use single AI persona - Atlas
        ai_persona = "Atlas"

        # Create AI message
        ai_message = {
            "message_id": f"ai_msg_{int(datetime.utcnow().timestamp() * 1000)}",
            "room_id": room_id,
            "user_id": None,
            "username": ai_persona,
            "message": ai_content,
            "content": ai_content,
            "message_type": "ai",
            "ai_persona": ai_persona,
            "ai_trigger": trigger.get("type"),
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Add to conversation history
        await redis_client.add_message_to_history(room_id, ai_message)

        # Broadcast to ALL users in room simultaneously
        logger.info(f"🤖 Broadcasting AI message to room {room_id}")
        await sio.emit("new_message", ai_message, room=room_id)

        logger.info(f"✅ AI response sent to room {room_id}")

    except Exception as e:
        logger.error(f"❌ Error generating AI response: {e}", exc_info=True)


async def monitor_room_silence(room_id: str):
    """
    Background task to monitor room silence and trigger AI engagement
    ENHANCED: Now tracks INDIVIDUAL user engagement, not just group silence
    """
    try:
        logger.info(f"🔍 Starting enhanced engagement monitor for room {room_id}")
        
        # Thresholds
        GROUP_SILENCE_THRESHOLD = 45  # Group silence: 45 seconds
        INDIVIDUAL_SILENCE_THRESHOLD = 120  # Individual silence: 2 minutes
        CHECK_INTERVAL = 20  # Check every 20 seconds
        
        while room_id in monitored_rooms:
            try:
                # Get room users
                users = await redis_client.get_room_users(room_id)
                
                if not users:
                    # Room is empty, stop monitoring
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue
                
                # Update silence duration for all users
                for user_id in users:
                    await context_manager.update_silence_duration(user_id)
                
                # PRIORITY 1: Check for GROUP BALANCE in multi-user rooms
                if len(users) >= 2:
                    # Multi-user room - check for quiet users
                    active_users = []
                    quiet_users = []
                    new_users = []
                    
                    for user_id in users:
                        user_context = await redis_client.get_user_context(user_id)
                        if user_context:
                            participation = user_context.get("participation", {})
                            silence_duration = participation.get("silence_duration", 0)
                            message_count = participation.get("message_count", 0)
                            
                            if message_count == 0:
                                new_users.append((user_id, user_context, silence_duration))
                            elif silence_duration > 90:  # Quiet for 90+ seconds
                                quiet_users.append((user_id, user_context, silence_duration))
                            else:
                                active_users.append((user_id, user_context))
                    
                    logger.info(f"👥 Room balance: {len(active_users)} active, {len(quiet_users)} quiet, {len(new_users)} new")
                    
                    # SCENARIO 1: New user joined but hasn't spoken (priority!)
                    if new_users:
                        for user_id, user_context, silence_duration in sorted(new_users, key=lambda x: x[2], reverse=True):
                            if silence_duration > 30:  # New user quiet for 30+ seconds
                                logger.info(f"🎯 NEW USER: {user_context.get('name')} hasn't participated yet ({silence_duration}s), including them")
                                
                                # Get active conversation topic
                                history = await redis_client.get_conversation_history(room_id, limit=5)
                                recent_topic = ""
                                if history:
                                    recent_msg = history[0].get('message', '')
                                    recent_topic = f"Recent topic: {recent_msg[:50]}"
                                
                                trigger = {
                                    "type": "new_user_inclusion",
                                    "priority": "high",
                                    "target_user": user_id,
                                    "user_id": user_id,
                                    "context": f"🎯 CRITICAL: {user_context.get('name')} is NEW and hasn't spoken yet. {recent_topic}. Welcome them warmly and ask them a simple, friendly question to include them. Use @{user_context.get('name')} and make it easy for them to jump in!"
                                }
                                
                                await generate_ai_response(room_id, trigger)
                                await asyncio.sleep(60)
                                break
                    
                    # SCENARIO 2: Existing user went quiet (someone is being left out)
                    elif quiet_users and len(active_users) > 0:
                        # Someone is quiet while others are talking
                        for user_id, user_context, silence_duration in sorted(quiet_users, key=lambda x: x[2], reverse=True):
                            if silence_duration >= INDIVIDUAL_SILENCE_THRESHOLD:
                                logger.info(f"🎯 QUIET USER: {user_context.get('name')} went quiet while others are talking ({silence_duration}s)")
                                
                                trigger = {
                                    "type": "balance_conversation",
                                    "priority": "medium",
                                    "target_user": user_id,
                                    "user_id": user_id,
                                    "context": f"🎯 GROUP BALANCE: {user_context.get('name')} was active but has been quiet for {int(silence_duration)}s while others are chatting. Bring them back into the conversation with @{user_context.get('name')} and ask about their thoughts on the current topic."
                                }
                                
                                await generate_ai_response(room_id, trigger)
                                await asyncio.sleep(60)
                                break
                
                # PRIORITY 2: Single user alone (different handling)
                elif len(users) == 1:
                    user_id = users[0]
                    user_context = await redis_client.get_user_context(user_id)
                    if user_context:
                        participation = user_context.get("participation", {})
                        silence_duration = participation.get("silence_duration", 0)
                        
                        # For single user, be more patient but still engage if too long
                        if silence_duration >= 60:  # 1 minute silence in 1-on-1
                            logger.info(f"🎯 SINGLE USER: {user_context.get('name')} quiet for {silence_duration}s, re-engaging")
                            
                            trigger = {
                                "type": "single_user_engagement",
                                "priority": "medium",
                                "target_user": user_id,
                                "user_id": user_id,
                                "context": f"User is alone and quiet. Ask an engaging question or share something interesting to restart the conversation."
                            }
                            
                            await generate_ai_response(room_id, trigger)
                            await asyncio.sleep(60)
                            continue
                
                # PRIORITY 2: Check for GROUP silence (only if no individual issues)
                history = await redis_client.get_conversation_history(room_id, limit=1)
                
                if history and len(history) > 0:
                    last_message = history[0]
                    last_timestamp = datetime.fromisoformat(last_message.get("timestamp"))
                    silence_duration = (datetime.utcnow() - last_timestamp).total_seconds()
                    
                    # If ENTIRE group has been silent
                    if silence_duration >= GROUP_SILENCE_THRESHOLD:
                        logger.info(f"🤫 Detected {silence_duration}s group silence in room {room_id}, triggering AI")
                        
                        trigger = {
                            "type": "group_silence",
                            "priority": "medium",
                            "context": f"Everyone has been quiet for {int(silence_duration)} seconds. Ask an engaging question related to the previous conversation to get everyone talking again."
                        }
                        
                        await generate_ai_response(room_id, trigger)
                        # Wait longer after AI response
                        await asyncio.sleep(90)
                    else:
                        # Check again after interval
                        await asyncio.sleep(CHECK_INTERVAL)
                else:
                    # No messages yet, wait
                    await asyncio.sleep(CHECK_INTERVAL)
                    
            except Exception as e:
                logger.error(f"❌ Error in silence monitor loop: {e}")
                await asyncio.sleep(CHECK_INTERVAL)
        
        logger.info(f"🔍 Stopping silence monitor for room {room_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in room silence monitor: {e}", exc_info=True)


def start_room_monitoring(room_id: str):
    """Start monitoring a room for silence"""
    if room_id not in monitored_rooms:
        monitored_rooms.add(room_id)
        # Create the background task
        asyncio.create_task(monitor_room_silence(room_id))
        logger.info(f"✅ Started monitoring room {room_id}")


def stop_room_monitoring(room_id: str):
    """Stop monitoring a room"""
    if room_id in monitored_rooms:
        monitored_rooms.discard(room_id)
        logger.info(f"🛑 Stopped monitoring room {room_id}")