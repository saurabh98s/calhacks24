from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ChatRealm"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False  # Disabled to prevent SQL logs in AI chat
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str
    
    # CORS
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:80"]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # AI Configuration (Optional - will use mock responses if not provided)
    ASI_ONE_API_KEY: str = "sk_e804d3f936f8458e852087496c6a3f99518478c238434aa5b3db67957fed4b5e"  # Fetch.ai API key
    ANTHROPIC_API_KEY: str = ""

    # Fetch.ai Agentverse Configuration
    ORCHESTRATOR_ADDRESS: str = "agent1qwyxpqax4rn7p8g0u8h337hcc0lwt0jj8j093jdyfhy8xgcyjuc4jupdart"  # Main orchestrator agent
    
    # AI Response Configuration
    MAX_CONTEXT_TOKENS: int = 25000
    DEFAULT_MAX_TOKENS: int = 500
    DEFAULT_TEMPERATURE: float = 0.8
    
    # User Activity Thresholds
    SILENCE_THRESHOLD_SECONDS: int = 120  # 2 minutes
    GROUP_SILENCE_THRESHOLD_SECONDS: int = 45
    ENGAGEMENT_CHECK_INTERVAL: int = 60  # 1 minute
    
    # Room Configuration
    MAX_USERS_PER_ROOM: int = 10
    CONVERSATION_HISTORY_LIMIT: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

