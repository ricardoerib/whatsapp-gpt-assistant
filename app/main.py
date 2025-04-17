import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .config import settings
from .api.routes import router
from .services.csv_processor import process_csv
from .services.user_profile import UserProfileService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting Application in {settings.APP_ENVIRONMENT} mode")
    process_csv()
    user_profile = UserProfileService()
    user_profile.initialize_database()
    yield
    # Shutdown
    logger.info("Shutting down application")

# Create FastAPI app
app = FastAPI(
    title="WhatsApp Chatbot API",
    description="API for WhatsApp Chatbot with LLM integration",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(router)

from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2, log_level="warning")