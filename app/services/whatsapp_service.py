import httpx
import logging
import json
from typing import Dict, List, Any, Optional
import uuid

from ..config import settings
from ..core.schema import ProcessedMessage, MessageType
from .user_profile import UserProfileService
from .llm_service import LLMService
from .audio_service import AudioService
from .utils import is_email_valid

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.api_url = settings.WHATSAPP_API_URL
        self.phone_number_id = settings.PHONE_NUMBER_ID
        self.base_url = f"{self.api_url}{self.phone_number_id}/messages"
        self.processed_messages = set()
        self.user_profile = UserProfileService()
        self.llm_service = LLMService()
        self.audio_service = AudioService()
    
    async def send_message(self, to: str, text: str) -> Dict:
        """Send a text message to a WhatsApp number"""
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
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
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                logger.info(f"Message sent successfully to {to}")
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} sending message: {e.response.text}")
                raise
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                raise
    
    async def download_media(self, media_id: str) -> bytes:
        """Download media from WhatsApp"""
        media_endpoint = f"https://graph.facebook.com/v21.0/{media_id}"
        
        async with httpx.AsyncClient() as client:
            try:
                # Get media URL
                headers = {"Authorization": f"Bearer {self.api_token}"}
                media_response = await client.get(media_endpoint, headers=headers)
                media_response.raise_for_status()
                
                media_data = media_response.json()
                media_url = media_data.get("url")
                
                if not media_url:
                    raise ValueError("Media URL not found in response")
                
                # Download the actual media
                media_response = await client.get(media_url, headers=headers)
                media_response.raise_for_status()
                
                return media_response.content
            except Exception as e:
                logger.error(f"Error downloading media {media_id}: {e}")
                raise
    
    def extract_webhook_data(self, payload: Dict) -> Dict:
        """Extract relevant data from webhook payload"""
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
            logger.error(f"Error extracting webhook data: {e}")
            return {}
    
    def process_message(self, raw_message: Dict, contacts: List[Dict]) -> Optional[ProcessedMessage]:
        """Process raw message into standardized format"""
        try:
            # Prevent duplicate processing
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
            logger.error(f"Error processing message: {e}")
            return None
            
    async def process_webhook(self, payload: Dict) -> List[Dict]:
        """Process webhook and return responses"""
        try:
            logger.info(f"Processing webhook...")
            
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
            logger.error(f"Error handling webhook: {e}")
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
            logger.error(f"Error handling message: {e}")
            return "Sorry, there was an error processing your message."
            
    async def handle_terms_flow(self, profile_id: str, message: ProcessedMessage, language: str) -> str:
        """Handle terms acceptance flow"""
        if not message.text_body:
            return self.get_translated_message("terms_required", language)
            
        #  Check if response is 1 or 2 1 - accept, 2 - reject
        # check the option to send whatsapp button !!!
        if message.text_body.lower() in ["1", "2"]:
            self.user_profile.accept_terms(profile_id)
            return self.get_translated_message("terms_accepted", language)
            
        return self.get_translated_message("terms_required", language)
    
    async def handle_email_flow(self, profile_id: str, message: ProcessedMessage, language: str) -> str:
        """Handle email collection flow"""
        if not message.text_body:
            return self.get_translated_message("request_email", language)
            
        if is_email_valid(message.text_body):
            self.user_profile.update_email(profile_id, message.text_body)
            return self.get_translated_message("email_saved", language)
            
        return self.get_translated_message("request_email", language)
    
    async def handle_text(self, profile_id: str, message: ProcessedMessage) -> str:
        """Handle text message"""
        if not message.text_body:
            return "Please send a text message."
        
        # Process message with LLM
        response = await self.llm_service.process_message(
            profile_id=profile_id,
            question=message.text_body
        )
        
        return response
    
    async def handle_audio(self, profile_id: str, message: ProcessedMessage) -> str:
        """Handle audio message"""
        try:
            if not message.media_id:
                return "Sorry, I couldn't process your audio message - no media ID found."
            
            logger.info(f"Processing audio message: {message.media_id}")
            
            # Download audio from WhatsApp
            audio_content = await self.download_media(message.media_id)
            
            # Save it to a temp file
            audio_file = await self.audio_service.download_audio(audio_content)
            
            # Transcribe the audio
            transcription = await self.audio_service.transcribe_audio(audio_file)
            
            if not transcription:
                return "I couldn't transcribe your audio message. Could you please send it again or type your message?"
            
            # Process the transcription with the LLM
            response = await self.llm_service.process_message(
                profile_id=profile_id,
                question=transcription
            )
            
            # Save interaction
            self.user_profile.save_interaction(profile_id, transcription, response)
            
            # Return combined response
            return f"🎤 *Transcrição:* {transcription}\n\n🤖 *Resposta:* {response}"
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            return "Sorry, I couldn't process your audio message. Please try again or send a text message instead."
    
    def get_translated_message(self, message_key: str, language: str) -> str:
        """Get translated message for predefined keys"""
        default_messages = {
            "welcome": "Welcome! Before continuing, we need your consent for GDPR. Do you agree? (Type '1' to accept)",
            "terms_required": "You need to accept the GDPR terms to continue. Type 'yes' to accept.",
            "terms_accepted": "Thank you for accepting the terms.",
            "request_email": "Please provide your email to complete your registration.",
            "email_saved": "Your email has been saved successfully. How can I assist you today?",
        }
        
        # For now, just return the English message
        # In a real implementation, you would use a translation service
        return default_messages.get(message_key, "Message not found")