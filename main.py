import uvicorn
from fastapi import (
    FastAPI, Depends, HTTPException, status, UploadFile, File, Form
)
import models
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse, FileResponse
from typing import List, Dict, Any
import io
import os

# Import your modules
import database
import crypto
import auth


# --- App Initialization ---
app = FastAPI(
    title="AetherSecure API",
    description="Backend for the Multi-Layer Crypto Vault",
    version="1.0.0"
)

# Initialize database on startup
@app.on_event("startup")
def on_startup():
    database.init_db()
    # Create a directory for temporary file responses
    if not os.path.exists("temp_files"):
        os.makedirs("temp_files")

# --- 1. Authentication Endpoints ---

@app.post("/register", response_model=models.UserInDB)
def register_user(user_in: models.UserCreate):
    """
    Register a new user.
    The client is expected to generate the face encoding and send it
    as a JSON string.
    """
    success, message = database.add_user(
        username=user_in.username,
        password=user_in.password,
        face_encoding_json=user_in.face_encoding_json
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # Return the created user info (excluding password)
    user_dict = {
        "username": user_in.username,
        "face_encoding_json": user_in.face_encoding_json
    }
    return user_dict


@app.post("/token", response_model=models.Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    Logs in a user by verifying *only* their username and password.
    
    **SECURITY NOTE:** Per your request, face verification is NOT
    performed here. The server trusts the client to have
    handled face verification *before* calling this endpoint.
    """
    user = database.authenticate_user(
        form_data.username, 
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(
        data={"sub": user['username']}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=models.UserInDB)
def read_users_me(
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Get information about the currently authenticated user.
    """
    return current_user

# --- 2. Crypto Tool Endpoints (Protected) ---

@app.post("/crypto/text/encrypt", response_model=Dict[str, str])
def encrypt_text(
    req: models.TextEncryptRequest,
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Encrypts plaintext using Super Encryption (Caesar + XOR + Base64).
    """
    try:
        ciphertext = crypto.super_encrypt_text(
            req.plaintext, req.caesar_shift, req.xor_key
        )
        return {"ciphertext": ciphertext}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crypto/text/decrypt", response_model=Dict[str, str])
def decrypt_text(
    req: models.TextDecryptRequest,
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Decrypts Super Encrypted text.
    """
    try:
        plaintext = crypto.super_decrypt_text(
            req.base64_ciphertext, req.caesar_shift, req.xor_key
        )
        return {"plaintext": plaintext}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {e}")

@app.post("/crypto/image/hide")
async def hide_stego_message(
    message: str = Form(...),
    image: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Hides a secret message in an image (LSB Steganography).
    Returns the new stego image.
    """
    if not image.filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="Only PNG images are supported.")
    
    try:
        image_bytes = await image.read()
        stego_image_bytes = crypto.stego_hide_message(image_bytes, message)
        
        # Return as a file stream
        return StreamingResponse(
            io.BytesIO(stego_image_bytes),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=stego_image.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crypto/image/extract", response_model=Dict[str, str])
async def extract_stego_message(
    image: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Extracts a secret message from a stego image.
    """
    try:
        stego_bytes = await image.read()
        extracted_message = crypto.stego_extract_message(stego_bytes)
        return {"message": extracted_message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crypto/file/encrypt")
async def encrypt_file_aes(
    password: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Encrypts a file using AES-256-GCM.
    Returns the encrypted file.
    """
    try:
        file_bytes = await file.read()
        encrypted_bytes = crypto.aes_encrypt_file(file_bytes, password)
        new_filename = f"{file.filename}.enc"
        
        return StreamingResponse(
            io.BytesIO(encrypted_bytes),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={new_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/crypto/file/decrypt")
async def decrypt_file_aes(
    password: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Decrypts an AES-256-GCM encrypted file.
    Returns the original file.
    """
    try:
        encrypted_file_bytes = await file.read()
        decrypted_bytes = crypto.aes_decrypt_file(encrypted_file_bytes, password)
        
        if file.filename.endswith(".enc"):
            new_filename = file.filename[:-4]
        else:
            new_filename = f"decrypted_{file.filename}"
            
        return StreamingResponse(
            io.BytesIO(decrypted_bytes),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={new_filename}"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=400, 
            detail="DECRYPTION FAILED. Password wrong or file corrupted."
        )

# --- 3. Secure Messaging Endpoints (Protected) ---

@app.get("/users", response_model=List[str])
def get_all_users(
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Gets a list of all usernames, excluding the current user.
    """
    return database.get_all_usernames(exclude_user=current_user['username'])

@app.get("/messages/inbox", response_model=List[models.MessageInDB])
def get_inbox(
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Gets the current user's message inbox (metadata only).
    """
    messages = database.get_messages_for_user(current_user['username'])
    return messages

@app.post("/messages/send/text", response_model=Dict[str, str])
def send_text_message(
    req: models.MessageSendText,
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Encrypts and sends a 'Super Encrypted Text' message.
    """
    try:
        encrypted_text = crypto.super_encrypt_text(
            req.plaintext, req.caesar_shift, req.xor_key
        )
        success, msg = database.send_message(
            sender=current_user['username'],
            recipient=req.recipient_username,
            msg_type="Teks Super Enkripsi",
            data=encrypted_text, # send_message will encode this string to bytes
            filename="pesan_teks.txt"
        )
        if not success:
            raise HTTPException(status_code=500, detail=msg)
        return {"detail": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/send/stego")
async def send_stego_message(
    recipient: str = Form(...),
    message: str = Form(...),
    image: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Creates and sends a Steganography image message.
    """
    if not image.filename.endswith(".png"):
        raise HTTPException(status_code=400, detail="Only PNG images are supported.")
    try:
        image_bytes = await image.read()
        stego_image_bytes = crypto.stego_hide_message(image_bytes, message)
        
        success, msg = database.send_message(
            sender=current_user['username'],
            recipient=recipient,
            msg_type="Gambar Steganografi",
            data=stego_image_bytes,
            filename=f"stego_{image.filename}"
        )
        if not success:
            raise HTTPException(status_code=500, detail=msg)
        return {"detail": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages/send/aes")
async def send_aes_message(
    recipient: str = Form(...),
    password: str = Form(...),
    file: UploadFile = File(...),
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Encrypts and sends an AES file message.
    """
    try:
        file_bytes = await file.read()
        encrypted_bytes = crypto.aes_encrypt_file(file_bytes, password)
        
        success, msg = database.send_message(
            sender=current_user['username'],
            recipient=recipient,
            msg_type="File AES",
            data=encrypted_bytes,
            filename=f"{file.filename}.enc"
        )
        if not success:
            raise HTTPException(status_code=500, detail=msg)
        return {"detail": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/messages/{message_id}/data")
async def get_message_data(
    message_id: int,
    current_user: models.UserInDB = Depends(auth.get_current_user)
):
    """
    Downloads the raw encrypted data/file for a specific message.
    The client is responsible for decrypting this.
    """
    message = database.get_message_by_id_for_user(
        message_id, current_user['username']
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized.")

    sender, msg_type, encrypted_data_blob, filename = message
    
    mime_type = "application/octet-stream"
    if msg_type == "Gambar Steganografi":
        mime_type = "image/png"
    elif msg_type == "Teks Super Enkripsi":
        mime_type = "text/plain"

    return StreamingResponse(
        io.BytesIO(encrypted_data_blob),
        media_type=mime_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# --- Run the app (for debugging) ---
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)