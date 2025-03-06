import os
import logging
from .utils import is_email_valid
from .gpt_client import get_response_from_gpt
from .wpp import send_whatsapp_message
from .user_profile import UserProfile
from .translations import get_translated_message
from pydantic import BaseModel
from typing import Optional, Dict, Any


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ENVIRONMENT = os.getenv("APP_ENVIRONMENT", "LOCAL").upper()
user_profile = UserProfile(APP_ENVIRONMENT)


def extract_message(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("text", {}).get("body", "")

def extract_phone_number(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [{}])[0].get("from", "")

def extract_sender_name(payload):
    return payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("contacts", [{}])[0].get("profile", {}).get("name", "")

def extract_messages(payload):
    messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    messages = [msg for msg in messages if "context" not in msg]
    return messages

def extract_audio_id(payload):
    messages = payload.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
    if messages:
        message = messages[0]
        if message.get("type") == "audio":
            return message.get("audio", {}).get("id", "")
    return None


async def validate_email_flow(profile_id, phone_number, language, message):
    if is_email_valid(message):
        user_profile.update_email(profile_id, message)
        await send_whatsapp_message(phone_number, get_translated_message("email_saved", language))
    else:
        await send_whatsapp_message(phone_number, get_translated_message("request_email", language))
    return

async def validate_terms_flow(profile_id, phone_number, language, message, user):
    if message.lower() in ["1", "accept", "yes"]:
        user_profile.accept_terms(profile_id)
        await send_whatsapp_message(phone_number, get_translated_message("terms_accepted", language))
        if not user.get("email"):
            validate_email_flow(profile_id, phone_number, language, message)
    else:
        await send_whatsapp_message(phone_number, get_translated_message("terms_required", language))
    return

async def handle_message(phone_number, name, message):
    user = user_profile.get_or_create_user(phone_number, name)
    user = dict(user) if user else None 
    profile_id = user.get("profile_id")
    language = user.get("language", "en") if user else "en"

    if not user.get("accepted_terms", False):
        await validate_terms_flow(profile_id, phone_number, language, message, user)
        return
    
    if not user.get("email"):
       await validate_email_flow(profile_id, phone_number, language, message)
       return

    
    if user.get("accepted_terms") and user.get("email"):
        response = get_response_from_gpt(profile_id, phone_number, message)
        await send_whatsapp_message(phone_number, response)


class WhatsAppMessage(BaseModel):
    message_id: str
    phone_number: str
    name: str
    text: Optional[str] = None
    audio_id: Optional[str] = None


async def process_whatsapp_message(body: Dict[Any, Any]) -> WhatsAppMessage:
    messages = extract_messages(body)
    if not messages:
        raise ValueError("No messages found in webhook body")
    
    message = messages[0]
    return WhatsAppMessage(
        message_id=message.get("id"),
        phone_number=extract_phone_number(body),
        name=extract_sender_name(body),
        text=extract_message(body),
        audio_id=extract_audio_id(body)
    )
