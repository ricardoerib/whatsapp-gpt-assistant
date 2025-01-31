import os
import logging
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from .utils import is_email_valid
from .csv_processor import process_csv

from .auth import decode_token, oauth2_scheme
from .gpt_client import get_response_from_gpt
from .wpp import send_whatsapp_message
from .user_profile import UserProfile
from .translations import get_translated_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def lifespan(app):
    yield

app = FastAPI(lifespan=lifespan)

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
user_profile = UserProfile(APP_ENVIRONMENT)

app = FastAPI()

class QuestionRequest(BaseModel):
    question: str
    overrideConfig: dict



@app.get("/")
def read_root():
    return {"message": "Its aliiiiiveeee!"}

@app.get("/error")
def read_root():
    raise Exception("Ihhh deu erro!!!")

@app.get("/healthcheck", response_class=PlainTextResponse)
def healthcheck():
    return "OK"

@app.post("/ask")
async def ask_question(request: QuestionRequest, token: str = Depends(oauth2_scheme)):
    if decode_token(token) is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session_id = request.overrideConfig.get("sessionId") if request.overrideConfig else 'anonymous'
    response = get_response_from_gpt(session_id, request.question)

    return {"response": response}

def extract_message(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("text", {}).get("body", "")

def extract_phone_number(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("from", "")

def extract_sender_name(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [{}])[0].get("profile", {}).get("name", "")

def extract_messages(payload):
    messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    return messages if len(messages) > 0 else None

async def handle_message(phone_number, name, message):
    # User onboarding setup
    user = user_profile.get_or_create_user(phone_number, name)
    user = dict(user) if user else None 
    profile_id = user.get("profile_id")
    language = user.get("language", "en") if user else "en"

    if not user.get("accepted_terms", False):
        if message.lower() in ["1", "accept", "yes"]:
            user_profile.accept_terms(profile_id)
            await send_whatsapp_message(phone_number, get_translated_message("terms_accepted", language))
        else:
            await send_whatsapp_message(phone_number, get_translated_message("terms_required", language))
        return
    
    if not user.get("email"):
        if is_email_valid(message):
            user_profile.update_email(profile_id, message)
            await send_whatsapp_message(phone_number, get_translated_message("email_saved", language))
        else:
            await send_whatsapp_message(phone_number, get_translated_message("request_email", language))
        return

                
    response = get_response_from_gpt(profile_id, phone_number, message)
    await send_whatsapp_message(phone_number, response)

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        messages = extract_messages(body)
        if messages:
            logger.info(f"body: {body}")

            name = extract_sender_name(body)
            phone_number = extract_phone_number(body)
            message = extract_message(body)
            
            logger.info(f"Message received from: {name}, Phone: {phone_number}\nMessage: {message}")

            await handle_message(phone_number, name, message)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")
    

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

