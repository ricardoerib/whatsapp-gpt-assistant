from app.logging_config import setup_logging
setup_logging()

import logging
from app.csv_processor import start_csv_watcher, process_csv
from app.auth import decode_token, oauth2_scheme
from app.gpt_client import get_response_from_gpt
from pydantic import BaseModel
from app.scheduler import start_scheduler
from app.wpp import send_whatsapp_message
from fastapi import Depends, FastAPI, HTTPException, Request
import httpx

logger = logging.getLogger(__name__)

async def lifespan(app):
    start_csv_watcher()
    process_csv()
    # start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)

class QuestionRequest(BaseModel):
    question: str
    overrideConfig: dict


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/error")
def read_root():
    raise Exception("Ihhh deu erro!!!")


@app.post("/ask")
async def ask_question(request: QuestionRequest, token: str = Depends(oauth2_scheme)):
    if decode_token(token) is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    session_id = request.overrideConfig.get("sessionId") if request.overrideConfig else 'anonymous'
    response = get_response_from_gpt(session_id, request.question)

    return {"response": response}


@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()

        entry = body.get("entry", [])
        if entry:
            changes = entry[0].get("changes", [])
            if changes:
                value = changes[0].get("value", {})
                messages = value.get("messages", [])
                
                if messages:
                    message = messages[0]
                    session_id = message["from"]
                    question = message.get("text", {}).get("body", "") 

                    print(f"Mensagem recebida de {session_id}: {question}")

                    response = get_response_from_gpt(session_id, request.question)

                    await send_whatsapp_message(session_id, response)

        return {"status": "success"}

    except Exception as e:
        print(f"Erro ao processar webhook: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar webhook")


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    VERIFY_TOKEN = "teste"
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("Webhook verificado")
        return challenge
    raise HTTPException(status_code=403, detail="Token de verificação inválido")


# def main():
#     logger.info("Starting the Application")
#     import uvicorn
#     logger.info("Starting Uvicorn server")
#     uvicorn.run(app, host="0.0.0.0", reload=True, port=8000)

# if __name__ == "__main__":
#     main()