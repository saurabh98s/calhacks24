import json
from typing import Any, Optional
from redis.asyncio import Redis
from app.config import settings


class RedisClient:
    def __init__(self):
        self.redis: Optional[Redis] = None
    
    async def connect(self):
        """Connect to Redis"""
        if self.redis is None:
            self.redis = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis
    
    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
    
    async def ping(self):
        """Test Redis connection"""
        if self.redis is None:
            await self.connect()
        return await self.redis.ping()
    
    # User Context Methods
    async def set_user_context(self, user_id: str, context: dict, ttl: int = 3600):
        """Store user context in Redis with 1 hour expiry"""
        if self.redis is None:
            await self.connect()
        key = f"user_context:{user_id}"
        # Set session expiry to 1 hour (3600 seconds)
        await self.redis.setex(key, ttl, json.dumps(context))
    
    async def get_user_context(self, user_id: str) -> Optional[dict]:
        """Retrieve user context from Redis"""
        if self.redis is None:
            await self.connect()
        key = f"user_context:{user_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_user_context(self, user_id: str):
        """Delete user context from Redis"""
        if self.redis is None:
            await self.connect()
        key = f"user_context:{user_id}"
        await self.redis.delete(key)
    
    # Room State Methods
    async def set_room_state(self, room_id: str, state: dict, ttl: int = 7200):
        """Store room state in Redis"""
        if self.redis is None:
            await self.connect()
        key = f"room_state:{room_id}"
        await self.redis.setex(key, ttl, json.dumps(state))
    
    async def get_room_state(self, room_id: str) -> Optional[dict]:
        """Retrieve room state from Redis"""
        if self.redis is None:
            await self.connect()
        key = f"room_state:{room_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def delete_room_state(self, room_id: str):
        """Delete room state from Redis"""
        if self.redis is None:
            await self.connect()
        key = f"room_state:{room_id}"
        await self.redis.delete(key)
    
    # Room Users Methods
    async def add_user_to_room(self, room_id: str, user_id: str):
        """Add user to room set"""
        if self.redis is None:
            await self.connect()
        key = f"room_users:{room_id}"
        await self.redis.sadd(key, user_id)
    
    async def remove_user_from_room(self, room_id: str, user_id: str):
        """Remove user from room set"""
        if self.redis is None:
            await self.connect()
        key = f"room_users:{room_id}"
        await self.redis.srem(key, user_id)
    
    async def get_room_users(self, room_id: str) -> list:
        """Get all users in a room"""
        if self.redis is None:
            await self.connect()
        key = f"room_users:{room_id}"
        return list(await self.redis.smembers(key))
    
    # Conversation History Methods
    async def add_message_to_history(self, room_id: str, message: dict):
        """Add message to room conversation history"""
        if self.redis is None:
            await self.connect()
        key = f"room_history:{room_id}"
        await self.redis.lpush(key, json.dumps(message))
        await self.redis.ltrim(key, 0, settings.CONVERSATION_HISTORY_LIMIT - 1)
    
    async def get_conversation_history(self, room_id: str, limit: int = 20) -> list:
        """Get recent conversation history"""
        if self.redis is None:
            await self.connect()
        key = f"room_history:{room_id}"
        messages = await self.redis.lrange(key, 0, limit - 1)
        return [json.loads(msg) for msg in messages]
    
    # Session Management
    async def set_session(self, session_id: str, data: dict, ttl: int = 86400):
        """Store session data"""
        if self.redis is None:
            await self.connect()
        key = f"session:{session_id}"
        await self.redis.setex(key, ttl, json.dumps(data))
    
    async def get_session(self, session_id: str) -> Optional[dict]:
        """Retrieve session data"""
        if self.redis is None:
            await self.connect()
        key = f"session:{session_id}"
        data = await self.redis.get(key)
        return json.loads(data) if data else None


# Create global Redis client instance
redis_client = RedisClient()

