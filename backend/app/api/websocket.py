"""
WebSocket handler using Socket.IO
"""
import socketio
import logging
from datetime import datetime
from uuid import UUID

from app.core.redis_client import redis_client
from app.services.context_manager import context_manager
from app.services.ai_service import ai_service
from app.services.user_service import user_service
from app.services.room_service import room_service
from app.core.database import AsyncSessionLocal
from app.utils.sentiment_analyzer import analyze_sentiment

logger = logging.getLogger(__name__)

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


@sio.event
async def join_room(sid, data):
    """Handle user joining a room"""
    try:
        room_id = data.get("room_id")
        user_id = data.get("user_id")
        username = data.get("username")
        
        logger.info(f"👤 User {username} joining room {room_id}")
        
        # Save session
        await sio.save_session(sid, {
            "room_id": room_id,
            "user_id": user_id,
            "username": username,
            **data
        })
        
        # Join Socket.IO room
        sio.enter_room(sid, room_id)
        
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
        
        # Notify room
        await sio.emit("user_joined", {
            "user_id": user_id,
            "username": username,
            "avatar_style": user_data["avatar_style"],
            "avatar_color": user_data["avatar_color"],
            "timestamp": datetime.utcnow().isoformat()
        }, room=room_id)
        
        # Get conversation history
        history = await redis_client.get_conversation_history(room_id, limit=50)
        
        # Send room data to user
        await sio.emit("room_joined", {
            "room_id": room_id,
            "message": "Successfully joined room",
            "conversation_history": history[::-1],  # Reverse to chronological order
            "active_users": users
        }, to=sid)
        
        # Check for new user trigger
        triggers = await context_manager.detect_triggers(room_id, user_id, "")
        
        for trigger in triggers:
            if trigger.get("type") == "new_user_joined":
                # Generate AI welcome
                await generate_ai_response(room_id, trigger)
        
    except Exception as e:
        logger.error(f"Error in join_room: {e}")
        await sio.emit("error", {"message": str(e)}, to=sid)


@sio.event
async def send_message(sid, data):
    """Handle user message"""
    try:
        room_id = data.get("room_id")
        user_id = data.get("user_id")
        username = data.get("username")
        message = data.get("message")
        
        logger.info(f"💬 Message from {username} in {room_id}: {message}")
        
        # Analyze sentiment
        sentiment, score = analyze_sentiment(message)
        
        # Update user context
        await context_manager.update_user_context(user_id, message, sentiment)
        
        # Create message object
        message_obj = {
            "message_id": f"msg_{datetime.utcnow().timestamp()}",
            "room_id": room_id,
            "user_id": user_id,
            "username": username,
            "message": message,
            "message_type": "user",
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add to conversation history
        await redis_client.add_message_to_history(room_id, message_obj)
        
        # Increment message counts
        async with AsyncSessionLocal() as db:
            user = await user_service.get_user_by_id(db, UUID(user_id))
            room = await room_service.get_room_by_room_id(db, room_id)
            
            if user:
                await user_service.increment_message_count(db, UUID(user_id))
            
            if room:
                await room_service.increment_message_count(db, room.id)
        
        # Broadcast message to room
        await sio.emit("new_message", message_obj, room=room_id)
        
        # Detect triggers for AI response
        triggers = await context_manager.detect_triggers(room_id, user_id, message)
        
        # Generate AI response if triggered
        for trigger in triggers:
            await generate_ai_response(room_id, trigger)
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
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
    """Generate AI response based on trigger"""
    try:
        logger.info(f"🤖 Generating AI response for trigger: {trigger.get('type')}")
        
        # Build prompt with context
        prompt_data = await context_manager.build_ai_prompt(room_id, trigger)
        
        if not prompt_data:
            logger.warning("No prompt data available")
            return
        
        # Generate AI response
        response = await ai_service.generate_response(
            messages=prompt_data.get("messages", []),
            max_tokens=prompt_data.get("max_tokens", 500),
            temperature=prompt_data.get("temperature", 0.8)
        )
        
        if not response:
            logger.warning("No AI response generated")
            return
        
        # Get room state for AI persona
        room_state = await redis_client.get_room_state(room_id)
        ai_persona = room_state.get("ai_persona", "assistant") if room_state else "assistant"
        
        # Create AI message object
        ai_message = {
            "message_id": f"ai_msg_{datetime.utcnow().timestamp()}",
            "room_id": room_id,
            "user_id": None,
            "username": ai_persona.title(),
            "message": response["content"],
            "message_type": "ai",
            "ai_persona": ai_persona,
            "ai_trigger": trigger.get("type"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add to conversation history
        await redis_client.add_message_to_history(room_id, ai_message)
        
        # Broadcast AI message
        await sio.emit("new_message", ai_message, room=room_id)
        
        logger.info(f"✅ AI response sent: {response['content'][:50]}...")
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")

