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
    """Handle client disconnection"""
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
        
        # Update active users count
        users = await redis_client.get_room_users(room_id)
        async with AsyncSessionLocal() as db:
            room = await room_service.get_room_by_room_id(db, room_id)
            if room:
                await room_service.update_active_users(db, room.id, len(users))
        
        # Stop monitoring if no users left
        if len(users) == 0:
            stop_room_monitoring(room_id)


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
        
        # Get user data from DB
        async with AsyncSessionLocal() as db:
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
            
            # Add user to room
            await context_manager.add_user_to_room(room_id, user_id, username)
            
            # Update room active users
            users = await redis_client.get_room_users(room_id)
            room = await room_service.get_room_by_room_id(db, room_id)
            if room:
                await room_service.update_active_users(db, room.id, len(users))
        
        # Get conversation history
        history = await redis_client.get_conversation_history(room_id, limit=50)
        
        # Send room data to user BEFORE notifying others
        await sio.emit("room_joined", {
            "room_id": room_id,
            "message": "Successfully joined room",
            "conversation_history": history[::-1],  # Reverse to chronological order
            "active_users": users
        }, to=sid)
        
        # Small delay to ensure client is ready
        await asyncio.sleep(0.1)
        
        # THEN notify room about new user
        await sio.emit("user_joined", {
            "user_id": user_id,
            "username": username,
            "avatar_style": user_data["avatar_style"],
            "avatar_color": user_data["avatar_color"],
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
        
        # Generate AI response if triggered (asynchronously, non-blocking)
        for trigger in triggers:
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
        
        # Get room state for AI persona
        room_state = await redis_client.get_room_state(room_id)
        ai_persona = room_state.get("ai_persona", "assistant") if room_state else "assistant"
        
        # Create AI message
        ai_message = {
            "message_id": f"ai_msg_{int(datetime.utcnow().timestamp() * 1000)}",
            "room_id": room_id,
            "user_id": None,
            "username": ai_persona.title(),
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
    Runs continuously while users are in the room
    """
    try:
        logger.info(f"🔍 Starting silence monitor for room {room_id}")
        
        # Silence threshold: 45 seconds of no messages
        SILENCE_THRESHOLD = 45
        CHECK_INTERVAL = 15  # Check every 15 seconds
        
        while room_id in monitored_rooms:
            try:
                # Get conversation history
                history = await redis_client.get_conversation_history(room_id, limit=1)
                
                if history and len(history) > 0:
                    last_message = history[0]
                    last_timestamp = datetime.fromisoformat(last_message.get("timestamp"))
                    silence_duration = (datetime.utcnow() - last_timestamp).total_seconds()
                    
                    # If group has been silent for threshold duration
                    if silence_duration >= SILENCE_THRESHOLD:
                        logger.info(f"🤫 Detected {silence_duration}s silence in room {room_id}, triggering AI")
                        
                        # Create group silence trigger
                        trigger = {
                            "type": "group_silence",
                            "priority": "medium",
                            "context": f"Group has been silent for {int(silence_duration)} seconds"
                        }
                        
                        # Generate AI response to re-engage
                        await generate_ai_response(room_id, trigger)
                        
                        # Wait longer after AI response to avoid spamming
                        await asyncio.sleep(120)
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