"""
Database initialization utilities
"""
import asyncio
from sqlalchemy import text
from app.core.database import engine, Base
from app.models import User, Room, Message
import logging

logger = logging.getLogger(__name__)


async def init_database():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created successfully")
            
        # Test connection
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            await conn.commit()
            logger.info("✅ Database connection test successful")
            
        return True
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


async def check_database_health():
    """Check if database is healthy"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            await conn.commit()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(init_database())

