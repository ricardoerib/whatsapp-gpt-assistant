import sqlite3
from datetime import datetime
import uuid
import logging

class SQLiteDB:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.conn = sqlite3.connect("./data/chatbot.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        self.logger.info("Creating tables...")
        cursor = self.conn.cursor()
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
        self.conn.commit()
        self.logger.info("Tables created successfully")

    def generate_profile_id():
        return str(uuid.uuid4())

    def get_or_create_user(self, phone_number, name):
        user = self.get_user(phone_number=phone_number)
        if user is None:
            profile_id = str(uuid.uuid4())
            self.register_user(profile_id=profile_id, name=name, phone_number=phone_number)
            return self.get_user(profile_id=profile_id) 
        return user

    def get_user(self, profile_id=None, phone_number=None):
        cursor = self.conn.cursor()
        if profile_id:
            cursor.execute("SELECT * FROM users WHERE profile_id = ?", (profile_id,))
        elif phone_number:
            cursor.execute("SELECT * FROM users WHERE phone_number = ?", (phone_number,))
        else:
            return None

        row = cursor.fetchone()
        return dict(row) if row else None  


    def register_user(self, profile_id, name, phone_number):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (profile_id, name, phone_number) VALUES (?, ?, ?)", (profile_id, name, phone_number))
        self.conn.commit()
        self.logger.info(f"User {name} created successfully")

    def accept_terms(self, profile_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET accepted_terms = TRUE WHERE profile_id = ?", (profile_id,))
        self.conn.commit()
        self.logger.info(f"Terms accepted successfully")

    def update_email(self, profile_id, email):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET email = ? WHERE profile_id = ?", (email, profile_id))
        self.conn.commit()
        self.logger.info(f"Email {email} updated successfully")

    def get_user_history(self, profile_id):
        #limit to last 10 interactions
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM interactions WHERE profile_id = ? ORDER BY created_at DESC LIMIT 10", (profile_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def save_interaction(self, profile_id, question, response):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO interactions (profile_id, question, response) VALUES (?, ?, ?)", (profile_id, question, response))
        self.conn.commit()
        self.logger.info("Interaction saved successfully")
