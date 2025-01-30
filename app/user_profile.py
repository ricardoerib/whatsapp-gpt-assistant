import os
from .db_sqlite import SQLiteDB
from .db_dynamodb import DynamoDBHandler

class UserProfile:
    def __init__(self, environment):
        self.environment = environment
        if environment == "PRODUCTION":
            self.db = DynamoDBHandler()
        else:
            self.db = SQLiteDB()

    def initialize_database(self):
        self.db.create_tables()

    def get_or_create_user(self, phone_number):
        return self.db.get_or_create_user(phone_number)

    def get_user(self, profile_id=None, phone_number=None):
        return self.db.get_user(profile_id, phone_number)

    def register_user(self, profile_id, phone_number):
        self.db.register_user(profile_id, phone_number)

    def accept_terms(self, profile_id):
        self.db.accept_terms(profile_id)

    def update_email(self, profile_id, email):
        self.db.update_email(profile_id, email)

    def save_interaction(self, profile_id, question, response):
        self.db.save_interaction(profile_id, question, response)

    def get_user_history(self, profile_id):
        return self.db.get_user_history(profile_id)
