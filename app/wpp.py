from pydantic import BaseModel
import logging
import os
import httpx
import io
import uuid
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
URL = f"{WHATSAPP_API_URL}{PHONE_NUMBER_ID}/messages"


class WhatsAppRequest(BaseModel):
    message: dict
    contacts: list

async def send_whatsapp_message(to, text):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "body": text
            }
        }
        try:
            response = await client.post(URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Message sent successfully:", response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise

async def send_whatsapp_message_group(contacts, text):
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": {
                "content": {
                    "type": "text",
                    "text": text
                }
            },
            "contacts": contacts
        }
        try:
            response = await client.post(URL, json=payload, headers=headers)
            response.raise_for_status()
            logger.info("Message sent successfully:", response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise


# async def transcribe_audio_message(media_id: str) -> str:
#     audio_file = await download_whatsapp_audio(media_id)
#     transcription_text = transcribe_audio(audio_file)
#     return transcription_text

async def download_whatsapp_audio(media_id: str) -> str:
    media_endpoint = f"https://graph.facebook.com/v21.0/{media_id}"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
    }
    
    async with httpx.AsyncClient() as client:
        media_response = await client.get(media_endpoint, headers=headers)
        media_response.raise_for_status()
        media_data = media_response.json()
        media_url = media_data.get("url")
        if not media_url:
            raise Exception("URL do áudio não encontrada nos dados de mídia.")

        audio_response = await client.get(media_url)
        audio_response.raise_for_status()
        audio_bytes = audio_response.content

    audio_file = io.BytesIO(audio_bytes)

    temp_filename = f"/tmp/{uuid.uuid4()}"
    audio_file.name = f"{temp_filename}.ogg"
    return audio_file