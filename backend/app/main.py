from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import socketio
import asyncio

from app.config import settings
from app.core.database import engine, Base, AsyncSessionLocal
from app.core.redis_client import redis_client
from app.api.routes import auth, rooms, users
from app.api.websocket import sio


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting ChatRealm backend...")
    
    # Wait for database to be ready
    max_retries = 10
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("✅ Database connected and tables created")
            break
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                print(f"❌ Database connection failed after {max_retries} attempts: {e}")
                raise
            print(f"⏳ Waiting for database... (attempt {retry_count}/{max_retries})")
            await asyncio.sleep(2)
    
    # Test Redis connection
    try:
        await redis_client.connect()
        await redis_client.ping()
        print("✅ Redis connected")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
    
    # Initialize default rooms
    try:
        from app.core.init_rooms import initialize_default_rooms
        async with AsyncSessionLocal() as session:
            await initialize_default_rooms(session)
    except Exception as e:
        print(f"⚠️  Warning: Failed to initialize default rooms: {e}")
    
    print("✅ ChatRealm backend started successfully!")
    
    yield
    
    # Shutdown
    print("👋 Shutting down ChatRealm backend...")
    await redis_client.close()
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(rooms.router, prefix="/api/rooms", tags=["Rooms"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])

# Mount Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    other_asgi_app=app,
    socketio_path="/socket.io"
)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    return {
        "message": "Welcome to ChatRealm API",
        "docs": "/docs",
        "health": "/health"
    }


# Export the socket app as the main app
app = socket_app

