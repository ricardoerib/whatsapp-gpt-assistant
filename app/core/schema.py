from pydantic import BaseModel, EmailStr, Field
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime

# Enumerations
class MessageType(str, Enum):
    """Types of messages supported by WhatsApp"""
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

# Authentication models
class TokenData(BaseModel):
    """Data stored in JWT token"""
    sub: str
    name: Optional[str] = None
    exp: int
    iat: int

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str

# User models
class UserBase(BaseModel):
    """Base user data shared by many endpoints"""
    name: str
    phone_number: str
    language: str = "en"

class UserCreate(UserBase):
    """Data required to create a new user"""
    email: Optional[EmailStr] = None

class UserUpdate(BaseModel):
    """Data that can be updated for a user"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    language: Optional[str] = None
    accepted_terms: Optional[bool] = None

class UserInDB(UserBase):
    """User as stored in the database"""
    profile_id: str
    email: Optional[EmailStr] = None
    accepted_terms: bool = False
    created_at: datetime

    class Config:
        orm_mode = True

# Interaction models
class Interaction(BaseModel):
    """User interaction with the chatbot"""
    question: str
    response: str
    created_at: datetime

    class Config:
        orm_mode = True

# Message models
class ProcessedMessage(BaseModel):
    """Internally processed message"""
    message_id: str
    phone_number: str
    timestamp: str
    type: MessageType
    text_body: Optional[str] = None
    media_id: Optional[str] = None
    contact_name: Optional[str] = None

# API request/response models
class QuestionRequest(BaseModel):
    """Request model for asking a question"""
    question: str
    overrideConfig: Dict[str, Any] = Field(default_factory=dict)

class QuestionResponse(BaseModel):
    """Response model for a question"""
    response: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str

class WebhookResponse(BaseModel):
    """Response model for webhook processing"""
    status: str

# WhatsApp webhook models
class WhatsAppContact(BaseModel):
    """Contact from WhatsApp webhook"""
    profile: Dict[str, Any]
    wa_id: str

class WhatsAppMessage(BaseModel):
    """Message from WhatsApp webhook"""
    from_: str = Field(..., alias="from")
    id: str
    timestamp: str
    type: str
    text: Optional[Dict[str, str]] = None
    image: Optional[Dict[str, Any]] = None
    audio: Optional[Dict[str, Any]] = None
    document: Optional[Dict[str, Any]] = None
    
    class Config:
        allow_population_by_field_name = True

class WhatsAppWebhook(BaseModel):
    """WhatsApp webhook payload"""
    object: str
    entry: List[Dict[str, Any]]
    
    def get_messages(self) -> List[WhatsAppMessage]:
        """Extract messages from the webhook payload"""
        if not self.entry:
            return []
            
        messages = []
        for entry in self.entry:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    messages.append(WhatsAppMessage(**msg))
                    
        return messages
    
    def get_contacts(self) -> List[WhatsAppContact]:
        """Extract contacts from the webhook payload"""
        if not self.entry:
            return []
            
        contacts = []
        for entry in self.entry:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for contact in value.get("contacts", []):
                    contacts.append(WhatsAppContact(**contact))
                    
        return contacts