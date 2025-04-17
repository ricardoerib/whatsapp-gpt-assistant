from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from ..core.schema import TokenData
from ..config import settings

logger = logging.getLogger(__name__)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=False  # Don't auto-raise errors for missing tokens
)

def create_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT token with the given data and expiration
    
    Args:
        data: Dictionary of claims to include in the token
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)  # Default 30 days
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    # Encode the token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm="HS256"
    )
    
    return encoded_jwt

def validate_token(token: str) -> Optional[TokenData]:
    """
    Validate and decode a JWT token
    
    Args:
        token: The JWT token to validate
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        # Remove Bearer prefix if present
        cleaned_token = token.replace("Bearer ", "") if token else ""
        
        # Decode the token
        payload = jwt.decode(
            cleaned_token, 
            settings.JWT_SECRET_KEY, 
            algorithms=["HS256"]
        )
        
        # Extract token data
        token_data = TokenData(
            sub=payload.get("sub"),
            name=payload.get("name"),
            exp=payload.get("exp"),
            iat=payload.get("iat")
        )
        
        # Check if token is expired
        if token_data.exp < datetime.utcnow().timestamp():
            logger.warning(f"Token expired for user {token_data.name}")
            return None
            
        return token_data
        
    except JWTError as e:
        logger.warning(f"JWT validation error: {e}")
        return None
    except ValidationError as e:
        logger.warning(f"Token data validation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error validating token: {e}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user from the token
    
    Args:
        token: JWT token from request
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not token:
        # For endpoints that support anonymous access
        return {"profile_id": "anonymous"}
    
    token_data = validate_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Could fetch more user data from database here if needed
    user_data = {
        "profile_id": token_data.sub,
        "name": token_data.name
    }
    
    return user_data

def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user from the token, if available
    
    Unlike get_current_user, this does not raise an exception if the token is missing
    
    Args:
        token: JWT token from request (optional)
        
    Returns:
        Dictionary with user information, or anonymous user
    """
    if not token:
        return {"profile_id": "anonymous"}
    
    token_data = validate_token(token)
    
    if not token_data:
        return {"profile_id": "anonymous"}
    
    # Could fetch more user data from database here if needed
    user_data = {
        "profile_id": token_data.sub,
        "name": token_data.name
    }
    
    return user_data

async def get_admin_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get the current user and verify they have admin privileges
    
    Args:
        token: JWT token from request
        
    Returns:
        Dictionary with user information
        
    Raises:
        HTTPException: If token is invalid, expired, or user is not an admin
    """
    user = await get_current_user(token)
    
    # Check if user has admin role
    # This would typically check a database or the token claims
    # For simplicity, we'll use a whitelist of admin profile_ids
    admin_ids = settings.ADMIN_USER_IDS.split(",") if settings.ADMIN_USER_IDS else []
    
    if user["profile_id"] not in admin_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource",
        )
    
    return user