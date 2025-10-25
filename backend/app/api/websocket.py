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
from app.core.database import AsyncSessionLocal
from app.utils.sentiment_analyzer import analyze_sentiment

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
        }
        
        # Add to conversation history FIRST
        await redis_client.add_message_to_history(room_id, message_obj)
        
        # Increment message counts
        async with AsyncSessionLocal() as db:
            user = await user_service.get_user_by_id(db, UUID(user_id))
            room = await room_service.get_room_by_room_id(db, room_id)
            
            if user:
                await user_service.increment_message_count(db, UUID(user_id))
            
            if room:
                await room_service.increment_message_count(db, room.id)
        
        # BROADCAST to ALL users in room
        logger.info(f"📤 Broadcasting message {message_obj['message_id']} to room {room_id}")
        
        # Verify room membership (debugging)
        room_sockets = sio.manager.rooms.get('/', {}).get(room_id, set())
        logger.info(f"🔍 Room '{room_id}' has {len(room_sockets)} sockets: {room_sockets}")
        
        # Emit to room
        await sio.emit("new_message", message_obj, room=room_id)
        
        logger.info(f"✅ Message broadcast complete for room {room_id}")
        
        # Detect triggers for AI response
        triggers = await context_manager.detect_triggers(room_id, user_id, message)
        
        # Generate AI response if triggered
        for trigger in triggers:
            # If user directly mentioned AI, respond IMMEDIATELY (not async)
            if trigger.get("priority") == "critical" or trigger.get("type") == "direct_mention":
                logger.info(f"🚨 CRITICAL TRIGGER: Responding immediately to direct AI mention")
                await generate_ai_response(room_id, trigger)
            else:
                # Other triggers can be async
                asyncio.create_task(generate_ai_response(room_id, trigger))
        
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


async def generate_ai_response(room_id: str, trigger: dict):
    """Generate AI response based on trigger - optimized for multi-user context"""
    try:
        logger.info(f"🤖 Generating AI response for room {room_id}, trigger: {trigger.get('type')}")
        
        # Build prompt with full multi-user context
        prompt_data = await context_manager.build_ai_prompt(room_id, trigger)
        
        if not prompt_data:
            logger.warning(f"No prompt data for room {room_id}")
            return
        
        # Generate AI response (async, non-blocking)
        response = await ai_service.generate_response(
            messages=prompt_data.get("messages", []),
            max_tokens=prompt_data.get("max_tokens", 500),
            temperature=prompt_data.get("temperature", 0.8)
        )
        
        if not response:
            logger.warning(f"No AI response generated for room {room_id}")
            return
        
        # Use single AI persona - Atlas
        ai_persona = "Atlas"
        
        # Create AI message
        ai_message = {
            "message_id": f"ai_msg_{int(datetime.utcnow().timestamp() * 1000)}",
            "room_id": room_id,
            "user_id": None,
            "username": ai_persona,
            "message": response["content"],
            "content": response["content"],
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
                
                # PRIORITY 1: Check for INDIVIDUAL users who need engagement
                for user_id in users:
                    user_context = await redis_client.get_user_context(user_id)
                    if user_context:
                        participation = user_context.get("participation", {})
                        silence_duration = participation.get("silence_duration", 0)
                        message_count = participation.get("message_count", 0)
                        
                        # If specific user has been silent AND has participated before
                        # OR if user hasn't participated at all (new user)
                        if message_count == 0 and silence_duration > 60:
                            # New user who hasn't spoken - gentle invitation
                            logger.info(f"🎯 User {user_context.get('name')} hasn't participated yet ({silence_duration}s), inviting them")
                            
                            trigger = {
                                "type": "individual_engagement",
                                "priority": "high",
                                "target_user": user_id,
                                "context": f"{user_context.get('name')} joined but hasn't participated yet. Gently invite them into the conversation with a direct question. Use @{user_context.get('name')} to tag them."
                            }
                            
                            await generate_ai_response(room_id, trigger)
                            # Wait before checking again
                            await asyncio.sleep(60)
                            break  # Only address one user at a time
                            
                        elif message_count > 0 and silence_duration >= INDIVIDUAL_SILENCE_THRESHOLD:
                            # Existing participant who went quiet
                            logger.info(f"🎯 User {user_context.get('name')} went quiet after participating ({silence_duration}s), re-engaging")
                            
                            trigger = {
                                "type": "individual_engagement",
                                "priority": "medium",
                                "target_user": user_id,
                                "context": f"{user_context.get('name')} was active but has been quiet for {int(silence_duration)} seconds. Reference their previous messages and ask a follow-up question to bring them back in. Use @{user_context.get('name')}."
                            }
                            
                            await generate_ai_response(room_id, trigger)
                            # Wait before checking again
                            await asyncio.sleep(60)
                            break  # Only address one user at a time
                
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