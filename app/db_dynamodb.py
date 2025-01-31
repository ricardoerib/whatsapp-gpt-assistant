import boto3
import os
import time
from datetime import datetime
from botocore.exceptions import ClientError
import uuid
import logging

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
            self.logger.info(f"[DynamoDB] A tabela '{DYNAMODB_TABLE}' já existe.")
            return
        
        self.logger.info(f"[DynamoDB] Criando a tabela '{DYNAMODB_TABLE}'...")
        
        try:
            table = dynamodb.create_table(
                TableName=DYNAMODB_TABLE,
                KeySchema=[
                    {"AttributeName": "profile_id", "KeyType": "HASH"}  # Chave primária
                ],
                AttributeDefinitions=[
                    {"AttributeName": "profile_id", "AttributeType": "S"}
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 5,
                    "WriteCapacityUnits": 5
                }
            )

            table.wait_until_exists()
            self.logger.info(f"[DynamoDB] Tabela '{DYNAMODB_TABLE}' criada com sucesso!")

        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao criar a tabela: {e}")

    def get_or_create_user(self, phone_number, name):
        user = self.get_user(phone_number=phone_number)
        if user is None:
            profile_id = str(uuid.uuid4())
            self.register_user(profile_id=profile_id, name=name, phone_number=phone_number)
            return self.get_user(profile_id=profile_id)

    def get_user(self, profile_id=None, phone_number=None):
        try:
            if profile_id:
                response = self.table.get_item(Key={"profile_id": profile_id})
                self.logger.info(f"[DynamoDB] Usuário encontrado: {response.get('Item')}")
                return response.get("Item")
            elif phone_number:
                response = self.table.scan(
                    FilterExpression="phone_number = :phone",
                    ExpressionAttributeValues={":phone": phone_number}
                )
                self.logger.info(f"[DynamoDB] Usuário encontrado: {response['Items'][0] if response['Items'] else None}")
                return response["Items"][0] if response["Items"] else None
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao buscar usuário: {e}")
            return None

    def register_user(self, profile_id, name, phone_number):
        try:
            self.table.put_item(Item={
                "profile_id": profile_id,
                "phone_number": phone_number,
                "name": name,
                "accepted_terms": False,
                "language": "en",
                "created_at": str(datetime.utcnow())
            })
            self.logger.info(f"[DynamoDB] Usuário {name} criado com sucesso!")
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao registrar usuário: {e}")

    def accept_terms(self, profile_id):
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET accepted_terms = :val",
                ExpressionAttributeValues={":val": True}
            )
            self.logger.info(f"[DynamoDB] Termos aceitos com sucesso!")
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao atualizar termos: {e}")

    def update_email(self, profile_id, email):
        try:
            self.table.update_item(
                Key={"profile_id": profile_id},
                UpdateExpression="SET email = :email",
                ExpressionAttributeValues={":email": email}
            )
            self.logger.info(f"[DynamoDB] E-mail atualizado com sucesso!")
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao atualizar e-mail: {e}")

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
            self.logger.info(f"[DynamoDB] Interação salva com sucesso!")
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao salvar interação: {e}")

    def get_user_history(self, profile_id):
        try:
            response = self.table.get_item(Key={"profile_id": profile_id})
            user = response.get("Item", {})
            self.logger.info(f"[DynamoDB] Histórico do usuário: {user.get('interactions', [])}")
            return user.get("interactions", []) if user else []
        except ClientError as e:
            self.logger.error(f"[DynamoDB] Erro ao buscar histórico: {e}")
            return []
