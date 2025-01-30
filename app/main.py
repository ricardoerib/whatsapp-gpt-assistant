import os
import logging
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
import uvicorn
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

def get_phone_number_from_body(body):
    entry = body.get("entry", [])
    if entry:
        changes = entry[0].get("changes", [])
        if changes:
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if messages:
                message = messages[0]
                return message["from"]
    return None

def get_message_from_body(body):
    entry = body.get("entry", [])
    if entry:
        changes = entry[0].get("changes", [])
        if changes:
            value = changes[0].get("value", {})
            messages = value.get("messages", [])
            
            if messages:
                message = messages[0]
                return message.get("text", {}).get("body", "") 
    return None

def extract_message(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("text", {}).get("body", "")

def extract_phone_number(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("from", "")

def extract_sender_name(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [{}])[0].get("profile", {}).get("name", "")

def extract_messages(payload):
    """Extrai a lista de mensagens do payload e verifica se há pelo menos uma mensagem."""
    messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    return messages if len(messages) > 0 else None

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        messages = extract_messages(body)
        if messages:
            print(f"body: {body}")

            name = extract_sender_name(body)
            phone_number = extract_phone_number(body)
            message = extract_message(body)
            
            print(f"Nome: {name}, Telefone: {phone_number}, Mensagem: {message}")

            logger.info(f"Mensagem recebida de {phone_number}")

            # user = user_profile.get_or_create_user(phone_number)

            # user = dict(user) if user else None 
            # language = user.get("language", "en") if user else "en"

            # if not user.get("accepted_terms", False):
            #     return {"message": get_translated_message("terms_required", language)}

            # if not user.get("email"):
            #     return {"message": get_translated_message("request_email", language)}

            response = get_response_from_gpt(phone_number, message)
            await send_whatsapp_message(phone_number, response)

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")

if __name__ == "__main__":
    logger.info(f"Starting Application in {APP_ENVIRONMENT} mode")
    process_csv()
    user_profile.initialize_database() 
    import uvicorn
    logger.info("Starting Uvicorn server")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, workers=2, log_level="warning")

