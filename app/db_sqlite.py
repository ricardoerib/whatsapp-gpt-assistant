import sqlite3
from datetime import datetime
import uuid

class SQLiteDB:
    def __init__(self):
        self.conn = sqlite3.connect("chatbot.db", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                profile_id TEXT PRIMARY KEY,
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

    def generate_profile_id():
        return str(uuid.uuid4())

    def get_or_create_user(self, phone_number):
        user = self.get_user(phone_number=phone_number)
        if user is None:
            profile_id = str(uuid.uuid4())
            self.register_user(profile_id=profile_id, phone_number=phone_number)
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


    def register_user(self, profile_id, phone_number):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (profile_id, phone_number) VALUES (?, ?)", (profile_id, phone_number))
        self.conn.commit()

    def accept_terms(self, profile_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET accepted_terms = TRUE WHERE profile_id = ?", (profile_id,))
        self.conn.commit()

    def update_email(self, profile_id, email):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE users SET email = ? WHERE profile_id = ?", (email, profile_id))
        self.conn.commit()
