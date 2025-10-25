"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.schemas.user_schema import UserCreate, UserResponse, UserLogin, Token
from app.services.user_service import user_service
from app.config import settings

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    
    # Check if username exists
    existing_user = await user_service.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = await user_service.create_user(db, user_data)
    
    return user


@router.post("/login", response_model=Token)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user"""
    
    # Get user
    user = await user_service.get_user_by_username(db, login_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/guest", response_model=Token)
async def guest_login(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create guest user"""
    
    # Ensure it's marked as guest
    user_data.is_guest = True
    user_data.password = None
    
    # Create user
    user = await user_service.create_user(db, user_data)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "is_guest": True}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

