from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import os
import json
import asyncio
from .utils import is_email_valid
from .wpp import send_whatsapp_message
from .user_profile import UserProfile
from .translations import get_translated_message
from .llm_assistant import get_gpt_client, GPTAssistantClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageType(Enum):
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    DOCUMENT = "document"
    VIDEO = "video"
    STICKER = "sticker"
    LOCATION = "location"
    CONTACTS = "contacts"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    UNKNOWN = "unknown"

class Contact(BaseModel):
    """Contact information from webhook"""
    profile: Dict[str, Any]
    wa_id: str

class ProcessedMessage(BaseModel):
    """Internally processed message"""
    message_id: str
    phone_number: str
    timestamp: str
    type: MessageType
    text_body: Optional[str] = None
    media_id: Optional[str] = None
    contact_name: Optional[str] = None

class WebhookProcessor:
    def __init__(self):
        self.user_profile = UserProfile(os.getenv("APP_ENVIRONMENT", "LOCAL").upper())
        self.processed_messages = set()

    def extract_webhook_data(self, payload: Dict) -> Dict:
        """Extract data from webhook payload"""
        try:
            if not payload.get("entry"):
                return {}

            result = {}
            entry = payload["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]
            
            result["messages"] = value.get("messages", [])
            result["contacts"] = value.get("contacts", [])
            
            return result
        except Exception as e:
            logger.error(f"Error extracting webhook data: {e}", exc_info=True)
            return {}

    def process_message(self, raw_message: Dict, contacts: List[Dict]) -> Optional[ProcessedMessage]:
        """Process raw message into internal format"""
        try:
            # Check if message already processed
            message_id = raw_message.get("id")
            if message_id in self.processed_messages:
                logger.info(f"Skipping already processed message: {message_id}")
                return None
                
            self.processed_messages.add(message_id)
            
            # Get message type
            msg_type = raw_message.get("type", "unknown")
            try:
                message_type = MessageType(msg_type)
            except ValueError:
                message_type = MessageType.UNKNOWN
                
            # Get contact name
            contact_name = "Unknown"
            if contacts and len(contacts) > 0:
                contact_name = contacts[0].get("profile", {}).get("name", "Unknown")
            
            # Create processed message
            processed = {
                "message_id": message_id,
                "phone_number": raw_message.get("from"),
                "timestamp": raw_message.get("timestamp"),
                "type": message_type,
                "contact_name": contact_name
            }
            
            # Process by message type
            if message_type == MessageType.TEXT:
                processed["text_body"] = raw_message.get("text", {}).get("body")
            
            elif message_type == MessageType.AUDIO:
                processed["media_id"] = raw_message.get("audio", {}).get("id")
                
            elif message_type == MessageType.IMAGE:
                processed["media_id"] = raw_message.get("image", {}).get("id")
                processed["text_body"] = raw_message.get("image", {}).get("caption")
                
            elif message_type == MessageType.DOCUMENT:
                processed["media_id"] = raw_message.get("document", {}).get("id")
                processed["text_body"] = raw_message.get("document", {}).get("caption")

            return ProcessedMessage(**processed)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return None

    async def handle_webhook(self, payload: Dict) -> List[Dict]:
        """Process webhook and return responses"""
        try:
            logger.info(f"Processing webhook: {json.dumps(payload, indent=2)[:500]}...")
            
            # Extract data
            data = self.extract_webhook_data(payload)
            if not data.get("messages"):
                logger.info("No messages to process")
                return []
                
            responses = []
            for raw_message in data["messages"]:
                message = self.process_message(raw_message, data.get("contacts", []))
                if not message:
                    continue
                    
                response = await self.handle_message(message)
                if response:
                    responses.append({
                        "recipient": message.phone_number, 
                        "message": response
                    })
                    
            return responses
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}", exc_info=True)
            return []

    async def handle_message(self, message: ProcessedMessage) -> Optional[str]:
        """Handle processed message"""
        try:
            # Get or create user
            user = self.user_profile.get_or_create_user(
                message.phone_number,
                message.contact_name
            )
            
            if not user:
                return "Sorry, I couldn't process your request."
                
            profile_id = user["profile_id"]
            language = user.get("language", "en")
            
            # Handle user flow
            if not user.get("accepted_terms", False):
                return await self.handle_terms_flow(profile_id, message, language)
                
            if not user.get("email"):
                return await self.handle_email_flow(profile_id, message, language)
                
            # Handle content based on type
            if message.type == MessageType.TEXT:
                return await self.handle_text(profile_id, message)
            elif message.type == MessageType.AUDIO:
                return await self.handle_audio(profile_id, message)
            else:
                return f"Received a {message.type.value} message. I can only process text and audio messages at the moment."
                
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return "Sorry, there was an error processing your message."

    async def handle_terms_flow(self, profile_id: str, message: ProcessedMessage, language: str) -> str:
        """Handle terms acceptance flow"""
        if not message.text_body:
            return get_translated_message("terms_required", language)
            
        if message.text_body.lower() in ["1", "accept", "yes", "sim", "aceito"]:
            self.user_profile.accept_terms(profile_id)
            return get_translated_message("terms_accepted", language)
            
        return get_translated_message("terms_required", language)

    async def handle_email_flow(self, profile_id: str, message: ProcessedMessage, language: str) -> str:
        """Handle email collection flow"""
        if not message.text_body:
            return get_translated_message("request_email", language)
            
        if is_email_valid(message.text_body):
            self.user_profile.update_email(profile_id, message.text_body)
            return get_translated_message("email_saved", language)
            
        return get_translated_message("request_email", language)

    async def handle_text(self, profile_id: str, message: ProcessedMessage) -> str:
        """Handle text message"""
        if not message.text_body:
            return "Please send a text message."
        
        # Get GPT client
        client = get_gpt_client()
        
        # Process message
        response = await client.process_message(
            profile_id=profile_id,
            question=message.text_body
        )
        
        return response

    async def handle_audio(self, profile_id: str, message: ProcessedMessage) -> str:
        """Handle audio message by downloading, transcribing and processing it"""
        try:
            if not message.media_id:
                return "Sorry, I couldn't process your audio message - no media ID found."
            
            logger.info(f"Processing audio message: {message.media_id}")
            
            # Get GPT client
            client = get_gpt_client()
            
            # Create tool call for audio download
            download_tool_call = type('ToolCall', (), {
                'function': type('Function', (), {
                    'name': 'handle_audio',
                    'arguments': json.dumps({
                        'operation': 'download',
                        'audio_id': message.media_id
                    })
                })
            })

            # Download audio
            audio_file = await client._execute_tool(download_tool_call)
            logger.info(f"Audio downloaded to: {audio_file}")
            
            if not audio_file:
                raise ValueError("Audio download failed")

            # Create tool call for transcription
            transcribe_tool_call = type('ToolCall', (), {
                'function': type('Function', (), {
                    'name': 'handle_audio',
                    'arguments': json.dumps({
                        'operation': 'transcribe',
                        'audio_id': audio_file
                    })
                })
            })

            # Transcribe audio
            transcription = await client._execute_tool(transcribe_tool_call)
            logger.info(f"Transcription completed: {transcription}")
            
            if not transcription:
                return "I couldn't transcribe your audio message. Could you please send it again or type your message?"
            
            # Process the transcription with GPT
            response = await client.process_message(
                profile_id=profile_id,
                question=transcription
            )
            
            # Save interaction
            self.user_profile.save_interaction(profile_id, transcription, response)
            
            # Return combined response
            return f"🎤 *Transcrição:* {transcription}\n\n🤖 *Resposta:* {response}"
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}", exc_info=True)
            return "Sorry, I couldn't process your audio message. Please try again or send a text message instead."

# Create processor instance
webhook_processor = WebhookProcessor()

# Main handler function for FastAPI
async def process_webhook(payload: Dict) -> List[Dict]:
    """Process webhook and return responses"""
    return await webhook_processor.handle_webhook(payload)