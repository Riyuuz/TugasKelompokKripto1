from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import models # Import your pydantic models
import database # Import your database functions

# --- CONFIGURATION ---
# !! IN A REAL APP, LOAD THIS FROM .env FILE !!
SECRET_KEY = "YOUR_SUPER_SECRET_KEY_CHANGE_THIS"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Password Hashing ---
# We use the one from crypto.py, but passlib is also standard
# Let's stick to your crypto.py for consistency.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# For this project, we'll call database.verify_password_bcrypt

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- Token Functions ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Dependency ---

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current user from a JWT.
    This protects endpoints.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = models.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get user data from database
    user = database.get_user_details(token_data.username)
    if user is None:
        raise credentials_exception
    
    # Return as a dictionary matching UserInDB model
    return {"username": user['username'], "face_encoding_json": user['face_encoding_json']}