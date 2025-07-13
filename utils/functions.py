from datetime import datetime, UTC, timedelta
from dotenv import load_dotenv
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
import os


load_dotenv()
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRES", 60))
SECRET_KEY = os.getenv("SECRETE_KEY")
ALGORITHM = os.getenv("ALGORITHM")
# Password hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Verify/Hash password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def generate_hash(password):
    return pwd_context.hash(password)

# Create access token
def generate_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Decode token
def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
