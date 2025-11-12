# schemas.py
from pydantic import BaseModel
from typing import Optional, List

# --- User & Auth Models ---

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    face_encoding_json: str # Client sends pre-computed encoding

class UserInDB(UserBase):
    face_encoding_json: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class UserDeleteConfirm(BaseModel):
    password: str

# --- Crypto Tool Models ---

class TextEncryptRequest(BaseModel):
    plaintext: str
    caesar_shift: int
    xor_key: str

class TextDecryptRequest(BaseModel):
    base64_ciphertext: str
    caesar_shift: int
    xor_key: str

# --- Messaging Models ---

class MessageSendText(BaseModel):
    recipient_username: str
    plaintext: str
    caesar_shift: int
    xor_key: str

class MessageInDB(BaseModel):
    id: int
    sender_username: str
    message_type: str
    original_filename: Optional[str] = None
    timestamp: str