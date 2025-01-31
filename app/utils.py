import pandas as pd
import markdown
from jose import jwt
import time
import os


def merge_duplicates(df):
    return df.groupby("response_id").agg(lambda x: x.dropna().iloc[0]).reset_index()

def get_instruction_prompt():
    with open("./data/instructions_prompt.md", "r") as f:
        return markdown.markdown(f.read())

def generate_jwt(username: str, user_id: str) -> str:
    SECRET_KEY = os.getenv("JWT_SECRET_KEY") 
    ALGORITHM = "HS256"

    payload = {
        "sub": user_id, # User ID
        "name": username, # User Name
        "iat": int(time.time()), 
        "exp": int(time.time()) + 3600 * 365 # 365 days
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def is_email_valid(email: str) -> bool:
    return "@" in email and "." in email

