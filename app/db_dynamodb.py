import boto3
import os
import time
from datetime import datetime
from botocore.exceptions import ClientError
import uuid
import logging
from dotenv import load_dotenv
load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
DYNAMODB_TABLE = os.getenv("DYNAMODB_TABLE", "chatbot_users")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)

class DynamoDBHandler:
    def __init__(self):
        self.table = dynamodb.Table(DYNAMODB_TABLE)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def create_tables(self):
        existing_tables = list(dynamodb.meta.client.list_tables()["TableNames"])

        if DYNAMODB_TABLE in existing_tables:
            self.logger.info(f"[DynamoDB] Table '{DYNAMODB_TABLE}' already exists.")
            return
        
        self.logger.info(f"[DynamoDB] Creating the table '{DYNAMODB_TABLE}'...")
        
        try:
            table = dynamodb.create_table(
                TableName=DYNAMODB_TABLE,
                KeySchema=[{"AttributeName": "profile_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "profile_id", "AttributeType": "S"}],
                ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            )

            table.wait_until_exists()
            self.logger.info(f"[DynamoDB] Table '{DYNAMODB_TABLE}' created successfully!")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error creating table: {e}")

    def get_or_create_user(self, phone_number, name):
        user = self.get_user(phone_number=phone_number)
        if user is None:
            profile_id = str(uuid.uuid4())
            self.register_user(profile_id=profile_id, name=name, phone_number=phone_number)
            return self.get_user(profile_id=profile_id)
        return user

    def get_user(self, profile_id=None, phone_number=None):
        try:
            if profile_id:
                response = self.table.get_item(Key={"profile_id": profile_id})
                user = response.get("Item")
                self.logger.info(f"[DynamoDB] User finded by profile_id: {user}")
                return user if user else None

            elif phone_number:
                response = self.table.scan(
                    FilterExpression="phone_number = :phone",
                    ExpressionAttributeValues={":phone": phone_number}
                )
                items = response.get("Items", [])
                user = items[0] if items else None
                self.logger.info(f"[DynamoDB] User finded by phone_number: {user}")
                return user

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error on get user: {e}")

        return None

    def register_user(self, profile_id, name, phone_number):
        try:
            user_data = {
                "profile_id": profile_id,
                "phone_number": phone_number,
                "name": name,
                "accepted_terms": False,
                "language": "en",
                "created_at": str(datetime.utcnow())
            }
            self.table.put_item(Item=user_data)
            self.logger.info(f"[DynamoDB] User {name} created successfully! profile_id: {profile_id}")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro creating user: {e}")

    def accept_terms(self, profile_id):
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET accepted_terms = :val",
                ExpressionAttributeValues={":val": True}
            )
            self.logger.info(f"[DynamoDB] Terms accepted profile_id {profile_id}!")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error updating terms: {e}")

    def update_email(self, profile_id, email):
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET email = :email",
                ExpressionAttributeValues={":email": email}
            )
            self.logger.info(f"[DynamoDB] E-mail updated by profile_id {profile_id}!")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error updating e-mail: {e}")

    def save_interaction(self, profile_id, question, response):
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET interactions = list_append(if_not_exists(interactions, :empty_list), :new_interaction)",
                ExpressionAttributeValues={
                    ":new_interaction": [{"question": question, "response": response, "timestamp": str(datetime.utcnow())}],
                    ":empty_list": []
                }
            )
            self.logger.info(f"[DynamoDB] Interaction saved for profile_id {profile_id}!")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error saving interaction: {e}")

    def get_user_history(self, profile_id):
        try:
            #limit to last 10 interactions
            response = self.table.get_item(Key={"profile_id": profile_id})
            interactions = response.get("Item", {}).get("interactions", [])
            self.logger.info(f"[DynamoDB] History recovered for profile_id {profile_id}!")
            return interactions[-10:]  # Return the last 10 interactions

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Error recovering history: {e}")
            return []
