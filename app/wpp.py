from pydantic import BaseModel
import os
import httpx

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
URL = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"



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
            print("Message sent successfully:", response.json())
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Request error: {e}")
            raise