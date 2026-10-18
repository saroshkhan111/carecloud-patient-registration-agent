import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv()

class Settings(BaseSettings):
    agent_id: str = os.getenv("AGENT_ID", "")
    elevenlabs_api_key: str = (
        os.getenv("ELEVENLABS_API_KEY")
        or os.getenv("ELEVENLABS_API__KEY")
        or ""
    )
    elevenlabs_tool_token: str = os.getenv("ELEVENLABS_TOOL_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./carecloud.db")
    environment: str = os.getenv("ENVIRONMENT", "local")
    reviewer_username: str = os.getenv("REVIEWER_USERNAME", "reviewer")
    reviewer_password: str = os.getenv("REVIEWER_PASSWORD", "reviewer-pass")
    phone_number: str = os.getenv("PHONE_NUMBER", "+1 (202) 555-0193")
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    class Config:
        env_file = ".env"
        extra = "allow"

settings = Settings()
