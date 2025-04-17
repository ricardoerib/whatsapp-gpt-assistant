import re
import logging
import markdown
import os
from typing import Optional, List, Dict, Any
from jose import jwt
import time

logger = logging.getLogger(__name__)

def is_email_valid(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: The email to validate
        
    Returns:
        True if the email is valid, False otherwise
    """
    # Basic email validation
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def get_instruction_prompt() -> str:
    """
    Get instruction prompt from markdown file
    
    This function reads an instruction prompt from a markdown file,
    converts it to HTML, and returns it.
    
    Returns:
        The instruction prompt converted to HTML
    """
    try:
        # Path to the instruction prompt
        prompt_path = "./data/instructions_prompt.md"
        
        # Check if file exists
        if not os.path.exists(prompt_path):
            logger.warning(f"Instructions prompt file not found at {prompt_path}")
            return "You are a helpful assistant."
            
        # Read and convert prompt
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt = f.read()
            
        # Convert markdown to HTML
        html_prompt = markdown.markdown(prompt)
        
        return html_prompt
        
    except Exception as e:
        logger.error(f"Error reading instruction prompt: {e}")
        return "You are a helpful assistant."

def merge_duplicates(df):
    """
    Merge duplicate rows in a DataFrame
    
    Args:
        df: DataFrame with potential duplicates
        
    Returns:
        DataFrame with duplicates merged
    """
    return df.groupby("response_id").agg(lambda x: x.dropna().iloc[0]).reset_index()

def generate_jwt(username: str, user_id: str, expiration_days: int = 365) -> str:
    """
    Generate a JWT token
    
    Args:
        username: The user's name or username
        user_id: The user's unique ID
        expiration_days: Number of days before token expires
        
    Returns:
        The generated JWT token
    """
    from ..config import settings
    
    SECRET_KEY = settings.JWT_SECRET_KEY
    ALGORITHM = "HS256"

    payload = {
        "sub": user_id,  # Subject (user ID)
        "name": username,  # User name
        "iat": int(time.time()),  # Issued at time
        "exp": int(time.time()) + (3600 * 24 * expiration_days)  # Expiry time
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def format_message_for_log(message: Dict[str, Any]) -> str:
    """
    Format a message for logging
    
    Args:
        message: The message to format
        
    Returns:
        Formatted message string
    """
    # Limit message length for logging
    max_length = 500
    
    if "text" in message and "body" in message["text"]:
        body = message["text"]["body"]
        if len(body) > max_length:
            body = body[:max_length] + "..."
        return f"Message: {body}"
    elif "audio" in message:
        return "Audio message"
    elif "image" in message:
        return "Image message"
    elif "document" in message:
        return "Document message"
    else:
        return "Unknown message type"

def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate a string to a maximum length
    
    Args:
        text: The text to truncate
        max_length: The maximum length
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."