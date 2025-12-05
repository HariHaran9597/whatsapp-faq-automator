# backend/config.py

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    
    # --- NEW SIMPLIFIED FIREBASE CONFIG ---
    FIREBASE_CREDENTIALS_PATH: str
    
    # --- API SECURITY ---
    # Optional API key for protecting sensitive endpoints
    # If not set, endpoint protection is disabled
    API_KEY: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

settings = Settings()