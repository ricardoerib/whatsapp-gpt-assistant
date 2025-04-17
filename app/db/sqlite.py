import sqlite3
import logging
import time
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from .base import DatabaseInterface
from ..config import settings

class SQLiteDatabase(DatabaseInterface):
    """SQLite implementation of the database interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use the configured database path or fallback to default
        db_path = settings.SQLITE_DB_PATH or "./data/chatbot.db"
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
    def create_tables(self) -> None:
        """Create necessary database tables"""
        try:
            self.logger.info("Creating SQLite tables...")
            cursor = self.conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    profile_id TEXT PRIMARY KEY,
                    name TEXT,
                    phone_number TEXT UNIQUE,
                    email TEXT,
                    accepted_terms BOOLEAN DEFAULT FALSE,
                    language TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Interactions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    profile_id TEXT,
                    question TEXT,
                    response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(profile_id) REFERENCES users(profile_id)
                )
            ''')
            
            # Index for faster querying
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_interactions_profile_id 
                ON interactions(profile_id)
            ''')
            
            self.conn.commit()
            self.logger.info("SQLite tables created successfully")
        except Exception as e:
            self.logger.error(f"Error creating tables: {e}")
            raise
            
    def get_user(self, profile_id: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by profile_id or phone_number"""
        try:
            cursor = self.conn.cursor()
            
            if profile_id:
                cursor.execute("SELECT * FROM users WHERE profile_id = ?", (profile_id,))
                self.logger.debug(f"Looking up user by profile_id: {profile_id}")
            elif phone_number:
                cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
                self.logger.debug(f"Looking up user by phone_number: {phone_number}")
            else:
                self.logger.warning("No profile_id or phone_number provided to get_user")
                return None
                
            row = cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            self.logger.error(f"Error getting user: {e}")
            return None
            
    def get_or_create_user(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Get a user or create if not exists"""
        try:
            user = self.get_user(phone_number=phone_number)
            
            if user is None:
                profile_id = str(uuid.uuid4())
                self.register_user(profile_id=profile_id, name=name, phone_number=phone_number)
                user = self.get_user(profile_id=profile_id)
                
            return user
        except Exception as e:
            self.logger.error(f"Error in get_or_create_user: {e}")
            raise
            
    def register_user(self, profile_id: str, name: str, phone_number: str) -> None:
        """Register a new user"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO users (profile_id, name, phone_number) VALUES (?, ?, ?)",
                (profile_id, name, phone_number)
            )
            self.conn.commit()
            self.logger.info(f"User {name} created with profile_id {profile_id}")
        except Exception as e:
            self.logger.error(f"Error registering user: {e}")
            self.conn.rollback()
            raise
            
    def accept_terms(self, profile_id: str) -> None:
        """Update a user's terms acceptance"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET accepted_terms = TRUE WHERE profile_id = ?",
                (profile_id,)
            )
            self.conn.commit()
            self.logger.info(f"Terms accepted for profile_id {profile_id}")
        except Exception as e:
            self.logger.error(f"Error accepting terms: {e}")
            self.conn.rollback()
            raise
            
    def update_email(self, profile_id: str, email: str) -> None:
        """Update a user's email"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "UPDATE users SET email = ? WHERE profile_id = ?",
                (email, profile_id)
            )
            self.conn.commit()
            self.logger.info(f"Email updated for profile_id {profile_id}")
        except Exception as e:
            self.logger.error(f"Error updating email: {e}")
            self.conn.rollback()
            raise
            
    def save_interaction(self, profile_id: str, question: str, response: str) -> None:
        """Save a user interaction"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO interactions (profile_id, question, response) VALUES (?, ?, ?)",
                (profile_id, question, response)
            )
            self.conn.commit()
            self.logger.info(f"Interaction saved for profile_id {profile_id}")
        except Exception as e:
            self.logger.error(f"Error saving interaction: {e}")
            self.conn.rollback()
            raise
            
    def get_user_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """Get a user's interaction history (last 10 interactions)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT * FROM interactions WHERE profile_id = ? ORDER BY created_at DESC LIMIT 10",
                (profile_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            self.logger.error(f"Error getting user history: {e}")
            return []