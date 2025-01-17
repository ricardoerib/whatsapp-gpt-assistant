from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def decode_token(token):
    try:
        striped = token.replace("Bearer ", "")
        payload = jwt.decode(striped, SECRET_KEY, algorithms=["HS256"])
        return payload
    except JWTError as e:
        print(f"JWT Error: {e}")
        return None