from typing import Optional, Dict, List, Any
import logging

from ..config import settings
from ..db.base import DatabaseInterface
from ..db.sqlite import SQLiteDatabase
from ..db.dynamodb import DynamoDBDatabase

class UserProfileService:
    """Service for managing user profiles"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Initialize the appropriate database based on the environment
        environment = settings.APP_ENVIRONMENT.upper()
        
        if environment == "PRODUCTION":
            self.logger.info("Using DynamoDB database")
            self.db: DatabaseInterface = DynamoDBDatabase()
        else:
            self.logger.info("Using SQLite database")
            self.db: DatabaseInterface = SQLiteDatabase()
            
    def initialize_database(self) -> None:
        """Initialize the database tables"""
        self.db.create_tables()
        
    def get_user(self, profile_id: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by profile_id or phone_number"""
        return self.db.get_user(profile_id, phone_number)
        
    def get_or_create_user(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Get a user or create if not exists"""
        return self.db.get_or_create_user(phone_number, name)
        
    def register_user(self, profile_id: str, name: str, phone_number: str) -> None:
        """Register a new user"""
        self.db.register_user(profile_id, name, phone_number)
        
    def accept_terms(self, profile_id: str) -> None:
        """Update a user's terms acceptance"""
        self.db.accept_terms(profile_id)
        
    def update_email(self, profile_id: str, email: str) -> None:
        """Update a user's email"""
        self.db.update_email(profile_id, email)
        
    def save_interaction(self, profile_id: str, question: str, response: str) -> None:
        """Save a user interaction"""
        self.db.save_interaction(profile_id, question, response)
        
    def get_user_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """Get a user's interaction history"""
        return self.db.get_user_history(profile_id)