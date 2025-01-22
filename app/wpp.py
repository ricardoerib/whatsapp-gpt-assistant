from pydantic import BaseModel
import requests
import os

WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")


class WhatsAppRequest(BaseModel):
    message: dict
    contacts: list

def send_whatsapp_message(to, text):
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {
            "body": text
        }
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to send WhatsApp message: {response.text}")
    return response.json()