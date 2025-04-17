import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Central configuration class for the application"""
    
    # Application settings
    APP_ENVIRONMENT: str = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Database settings
    DATABASE_ENABLED: bool = os.getenv("DATABASE_ENABLED", "false").lower() == "true"
    
    # AWS settings
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # DynamoDB settings
    DYNAMODB_TABLE: str = os.getenv("DYNAMODB_TABLE", "chatbot_users")
    
    # SQLite settings
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./data/chatbot.db")
    
    # WhatsApp settings
    WHATSAPP_API_TOKEN: str = os.getenv("WHATSAPP_API_TOKEN", "")
    WHATSAPP_API_URL: str = os.getenv("WHATSAPP_API_URL", "")
    PHONE_NUMBER_ID: str = os.getenv("PHONE_NUMBER_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "teste")
    
    # LLM settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GPT_MODEL: str = os.getenv("GPT_MODEL", "gpt-4-turbo-preview")
    FALLBACK_ASSISTANT_ID: str = os.getenv("FALLBACK_ASSISTANT_ID", "")
    
    # Authentication settings
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    ADMIN_USER_IDS: str = os.getenv("ADMIN_USER_IDS", "")
    
    # CSV processing
    CSV_FILE_PATH: str = os.getenv("CSV_FILE_PATH", "./data/vx_questions_results.csv")

# Create a global settings instance
settings = Settings()