from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App
    APP_NAME: str = "Omni-Channel CRM"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"
    # Public origin of this API (used in iframe embed snippets/webhook URLs)
    PUBLIC_BASE_URL: str = "http://localhost:8000"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/omnicrm"
    DATABASE_SYNC_URL: str = "postgresql://postgres:postgres@localhost:5432/omnicrm"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Auth
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Twilio
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_PHONE_NUMBER: Optional[str] = None
    TWILIO_WEBHOOK_URL: Optional[str] = None
    
    # SendGrid
    SENDGRID_API_KEY: Optional[str] = None
    SENDGRID_FROM_EMAIL: Optional[str] = None
    
    # AI Providers
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    AI_PROVIDER: str = "anthropic"  # anthropic, openai, ollama
    AI_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # Ollama (local AI)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    
    # White-label branding defaults (DB row is seeded from these and can be
    # changed live from the admin configuration dashboard)
    BRAND_COMPANY_NAME: str = "LeadStack"
    BRAND_LOGO_DARK_URL: Optional[str] = None
    BRAND_LOGO_LIGHT_URL: Optional[str] = None
    BRAND_PRIMARY_COLOR: str = "#8B5CF6"
    BRAND_ACCENT_COLOR: str = "#C084FC"
    BRAND_CUSTOM_DOMAIN: Optional[str] = None

    # Compliance
    QUIET_HOURS_START: int = 21  # 9 PM
    QUIET_HOURS_END: int = 8    # 8 AM
    DEFAULT_TIMEZONE: str = "America/Denver"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
