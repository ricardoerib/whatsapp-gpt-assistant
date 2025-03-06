import os
import logging
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from fastapi.background import BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json

from .csv_processor import process_csv
from .auth import decode_token, oauth2_scheme
from .user_profile import UserProfile
from .messages import process_webhook
from .wpp import send_whatsapp_message
from .llm_assistant import GPTAssistantClient, get_gpt_client


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def lifespan(app):
    yield

app = FastAPI(lifespan=lifespan)

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
user_profile = UserProfile(APP_ENVIRONMENT)

app = FastAPI()
client = GPTAssistantClient()

processed_messages = set()

class QuestionRequest(BaseModel):
    question: str
    overrideConfig: dict


class HealthResponse(BaseModel):
    status: str

class QuestionResponse(BaseModel):
    response: str

@app.get("/healthcheck", response_model=HealthResponse)
def healthcheck():
    return {"status": "OK"}


@app.post("/ask")
async def ask_question(request: QuestionRequest, token: str = Depends(oauth2_scheme)):
    # if decode_token(token) is None:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    profile_id = request.overrideConfig.get("profile_id") if request.overrideConfig else 'anonymous'
    text = request.question

    response = await client.process_message(
        profile_id=profile_id,
        question=text,
    )

    return {"response": response}



@app.post("/webhook")
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    try:
        body = await request.json()
        # logger.info(f"Received webhook: {json.dumps(body, indent=2)[:500]}...")

        if "statuses" in str(body):
            logger.info("Received status update - ignoring")
            return {"status": "success"}
        
        responses = await process_webhook(body)
        
        for response in responses:
            background_tasks.add_task(
                send_whatsapp_message,
                response["recipient"],
                response["message"]
            )
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/webhook", response_class=PlainTextResponse)
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    VERIFY_TOKEN = "teste"
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge
    raise HTTPException(status_code=403, detail="Verification token invalid")

def main():
    logger.info(f"Starting Application in {APP_ENVIRONMENT} mode")
    process_csv()
    user_profile.initialize_database()
    
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2, log_level="warning")
    logger.info("Uvicorn server started")

if __name__ == "__main__":
    main()

