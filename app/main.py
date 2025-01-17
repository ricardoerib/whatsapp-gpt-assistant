from app.logging_config import setup_logging
setup_logging()

import logging
from app.csv_processor import start_csv_watcher, process_csv
from app.auth import decode_token, oauth2_scheme
from app.gpt_client import get_response_from_gpt
from pydantic import BaseModel
from app.scheduler import start_scheduler
from fastapi import Depends, FastAPI, HTTPException

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


# def main():
#     logger.info("Starting the Application")
#     import uvicorn
#     logger.info("Starting Uvicorn server")
#     uvicorn.run(app, host="0.0.0.0", port=8000)

# if __name__ == "__main__":
#     main()