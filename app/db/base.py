from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

class DatabaseInterface(ABC):
    """Abstract interface for database operations"""
    
    @abstractmethod
    def create_tables(self) -> None:
        """Create necessary database tables"""
        pass
        
    @abstractmethod
    def get_user(self, profile_id: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by profile_id or phone_number"""
        pass
        
    @abstractmethod
    def get_or_create_user(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Get a user or create if not exists"""
        pass
        
    @abstractmethod
    def register_user(self, profile_id: str, name: str, phone_number: str) -> None:
        """Register a new user"""
        pass
        
    @abstractmethod
    def accept_terms(self, profile_id: str) -> None:
        """Update a user's terms acceptance"""
        pass
        
    @abstractmethod
    def update_email(self, profile_id: str, email: str) -> None:
        """Update a user's email"""
        pass
        
    @abstractmethod
    def save_interaction(self, profile_id: str, question: str, response: str) -> None:
        """Save a user interaction"""
        pass
        
    @abstractmethod
    def get_user_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """Get a user's interaction history"""
        pass