import boto3
import time
import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table("FinancialBotData")

def save_interaction(session_id, question, answer, full_response):
    try:
        table.put_item(Item={
            "session_id": session_id if session_id else "anonymous",
            "question": question,
            "answer": answer,
            "full_response": full_response,
            "timestamp": int(time.time())
        })
    except Exception as e:
        print(f"Error on saving interaction: {e}")
        return False

def get_user_history(session_id):
    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('sessionId').eq(session_id),
            ScanIndexForward=True 
        )
        items  = response.get('Items', [])
        return [item['question' + ": "+ item['answer']] for item in items]
    except Exception as e:
        print(f"Error on getting user history: {e}")
        return False