import boto3
import logging
import time
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from typing import Optional, List, Dict, Any
from .base import DatabaseInterface
from ..config import settings

class DynamoDBDatabase(DatabaseInterface):
    """DynamoDB implementation of the database interface"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize DynamoDB client
        self.dynamodb = boto3.resource(
            "dynamodb", 
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
        )
        
        self.table_name = settings.DYNAMODB_TABLE
        self.table = self.dynamodb.Table(self.table_name)
        
    def create_tables(self) -> None:
        """Create DynamoDB table if it doesn't exist"""
        try:
            # Check if table exists
            existing_tables = list(self.dynamodb.meta.client.list_tables()["TableNames"])
            
            if self.table_name in existing_tables:
                self.logger.info(f"DynamoDB table '{self.table_name}' already exists.")
                return
                
            self.logger.info(f"Creating DynamoDB table '{self.table_name}'...")
            
            # Create the table
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[{"AttributeName": "profile_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "profile_id", "AttributeType": "S"}],
                ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5}
            )
            
            # Wait for table to be created
            table.wait_until_exists()
            self.logger.info(f"DynamoDB table '{self.table_name}' created successfully.")
            
        except ClientError as e:
            self.logger.error(f"Error creating DynamoDB table: {e}")
            raise
            
    def get_user(self, profile_id: Optional[str] = None, phone_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a user by profile_id or phone_number"""
        try:
            if profile_id:
                response = self.table.get_item(Key={"profile_id": profile_id})
                user = response.get("Item")
                return user
                
            elif phone_number:
                # Scan the table for the phone number (not efficient, but necessary)
                response = self.table.scan(
                    FilterExpression="phone_number = :phone",
                    ExpressionAttributeValues={":phone": phone_number}
                )
                
                items = response.get("Items", [])
                return items[0] if items else None
                
            return None
            
        except ClientError as e:
            self.logger.error(f"Error getting user from DynamoDB: {e}")
            return None
            
    def get_or_create_user(self, phone_number: str, name: str) -> Dict[str, Any]:
        """Get a user or create if not exists"""
        user = self.get_user(phone_number=phone_number)
        
        if user is None:
            profile_id = str(uuid.uuid4())
            self.register_user(profile_id, name, phone_number)
            return self.get_user(profile_id=profile_id)
            
        return user
        
    def register_user(self, profile_id: str, name: str, phone_number: str) -> None:
        """Register a new user"""
        try:
            user_data = {
                "profile_id": profile_id,
                "phone_number": phone_number,
                "name": name,
                "accepted_terms": False,
                "language": "en",
                "created_at": str(datetime.utcnow()),
                "interactions": []  # Initialize empty interactions list
            }
            
            self.table.put_item(Item=user_data)
            self.logger.info(f"User {name} registered in DynamoDB with profile_id {profile_id}")
            
        except ClientError as e:
            self.logger.error(f"Error registering user in DynamoDB: {e}")
            raise
            
    def accept_terms(self, profile_id: str) -> None:
        """Update a user's terms acceptance"""
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET accepted_terms = :val",
                ExpressionAttributeValues={":val": True}
            )
            self.logger.info(f"Terms accepted for profile_id {profile_id}")
            
        except ClientError as e:
            self.logger.error(f"Error accepting terms in DynamoDB: {e}")
            raise
            
    def update_email(self, profile_id: str, email: str) -> None:
        """Update a user's email"""
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET email = :email",
                ExpressionAttributeValues={":email": email}
            )
            self.logger.info(f"Email updated for profile_id {profile_id}")
            
        except ClientError as e:
            self.logger.error(f"Error updating email in DynamoDB: {e}")
            raise
            
    def save_interaction(self, profile_id: str, question: str, response: str) -> None:
        """Save a user interaction"""
        try:
            # Using list_append to add to the interactions array
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET interactions = list_append(if_not_exists(interactions, :empty_list), :new_interaction)",
                ExpressionAttributeValues={
                    ":new_interaction": [{
                        "question": question,
                        "response": response,
                        "timestamp": str(datetime.utcnow())
                    }],
                    ":empty_list": []
                }
            )
            self.logger.info(f"Interaction saved for profile_id {profile_id}")
            
        except ClientError as e:
            self.logger.error(f"Error saving interaction in DynamoDB: {e}")
            raise
            
    def get_user_history(self, profile_id: str) -> List[Dict[str, Any]]:
        """Get a user's interaction history (last 10 interactions)"""
        try:
            response = self.table.get_item(Key={"profile_id": profile_id})
            user = response.get("Item", {})
            interactions = user.get("interactions", [])
            
            # Return the last 10 interactions
            return interactions[-10:] if interactions else []
            
        except ClientError as e:
            self.logger.error(f"Error getting user history from DynamoDB: {e}")
            return []