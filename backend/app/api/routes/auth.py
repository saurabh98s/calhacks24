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
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/scrape-linkedin")
async def scrape_linkedin(data: dict):
    """Preview LinkedIn profile data before user creation"""
    linkedin_url = data.get("linkedin_url")
    
    if not linkedin_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="LinkedIn URL is required"
        )
    
    try:
        from app.services.linkedin_scraper import scrape_linkedin_profile
        logger.info(f"🔍 Previewing LinkedIn profile: {linkedin_url}")
        
        profile_data = await scrape_linkedin_profile(linkedin_url)
        
        if not profile_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to scrape LinkedIn profile. Please check the URL and try again."
            )
        
        return profile_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ LinkedIn scraping error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error scraping LinkedIn: {str(e)}"
        )


@router.post("/validate-username")
async def validate_username(
    username: str,
    room_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Validate if username is available in specific room"""
    existing_user = await user_service.get_user_by_username_and_room(
        db, username, room_id
    )
    
    if existing_user:
        return {
            "available": False,
            "message": f"Username '{username}' is already taken in this room"
        }
    
    return {
        "available": True,
        "message": "Username is available"
    }


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
    """Create guest user with room-specific username validation and optional LinkedIn scraping"""
    
    # Ensure it's marked as guest
    user_data.is_guest = True
    user_data.password = None
    
    # Check if username exists in THIS specific room
    if user_data.room_id:
        existing_user = await user_service.get_user_by_username_and_room(
            db, user_data.username, user_data.room_id
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{user_data.username}' is already taken in this room. Please choose another."
            )
    
    # Scrape LinkedIn profile if URL provided
    if user_data.linkedin_url:
        try:
            from app.services.linkedin_scraper import scrape_linkedin_profile
            logger.info(f"🔍 Scraping LinkedIn for user: {user_data.username}")
            profile_data = await scrape_linkedin_profile(user_data.linkedin_url)
            
            if profile_data and profile_data.get("persona"):
                user_data.persona = profile_data["persona"]
                logger.info(f"✅ Persona generated: {user_data.persona[:100]}...")
            else:
                logger.warning(f"⚠️ Failed to generate persona from LinkedIn")
        except Exception as e:
            logger.error(f"❌ LinkedIn scraping error: {e}")
            # Continue without persona - don't block user creation
    
    # Create user with room assignment and persona
    user = await user_service.create_user(db, user_data)
    
    # Create access token
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "is_guest": True}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

