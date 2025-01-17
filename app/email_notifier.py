import boto3
import os
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

ses = boto3.client("ses", region_name=AWS_REGION)

def send_email(subject, body):
    ses.send_email(
        Source="admin@example.com",
        Destination={"ToAddresses": ["admin@example.com"]},
        Message={
            "Subject": {"Data": subject},
            "Body": {"Text": {"Data": body}}
        }
    )
