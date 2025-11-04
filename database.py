# database.py
import sqlite3
import bcrypt # Using bcrypt from crypto.py's logic
import json
import datetime

# Import password functions from your existing crypto file
from crypto import hash_password_bcrypt, verify_password_bcrypt

DATABASE_FILE = 'users.db'

# --- 1. Database Initialization (Modified) ---

def init_db():
    """Membuat tabel users DAN messages."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Tabel Users (Tetap Sama, field face_encoding_json akan
    # menyimpan string JSON yang di-supply client)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        face_encoding_json TEXT
    );
    ''')
    
    # Tabel Messages (Tetap Sama)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_username TEXT NOT NULL,
        recipient_username TEXT NOT NULL,
        message_type TEXT NOT NULL, 
        encrypted_data BLOB NOT NULL,
        original_filename TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER DEFAULT 0,
        FOREIGN KEY (sender_username) REFERENCES users (username),
        FOREIGN KEY (recipient_username) REFERENCES users (username)
    );
    ''')
    
    conn.commit()
    conn.close()
    print("Database 'users.db' dan 'messages.db' berhasil diinisialisasi.")

# --- 2. User & Auth Functions (MODIFIED) ---

def add_user(username, password, face_encoding_json):
    """
    Menambahkan pengguna baru dengan HASH password dan 
    FACE ENCODING (sebagai string) yang sudah jadi.
    """
    if not username or not password or not face_encoding_json:
        return False, "Data tidak lengkap."
    try:
        # Client sudah memvalidasi encoding, server hanya menyimpan
        password_hash = hash_password_bcrypt(password)
        
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, face_encoding_json) VALUES (?, ?, ?)", 
                       (username, password_hash, face_encoding_json))
        conn.commit()
        conn.close()
        return True, "Registrasi berhasil."
    except sqlite3.IntegrityError:
        return False, f"Username '{username}' sudah ada."
    except Exception as e:
        return False, f"Error: {e}"

def authenticate_user(username, password):
    """
    Memverifikasi login pengguna HANYA DENGAN password.
    Mengembalikan data user jika berhasil, None jika gagal.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, face_encoding_json FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        stored_hash, stored_face_encoding_json = result[0], result[1]
        
        # Verifikasi HANYA password
        if verify_password_bcrypt(password, stored_hash):
            return {
                "username": username, 
                "face_encoding_json": stored_face_encoding_json
            }
    return None

def get_user_details(username):
    """
    Mengambil detail user berdasarkan username (untuk auth).
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, face_encoding_json FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return {"username": result[0], "face_encoding_json": result[1]}
    return None

# --- 3. FUNGSI-FUNGSI PESAN (Tetap Sama, tapi ditambah 1) ---

def get_all_usernames(exclude_user=None):
    """Mengambil semua username dari tabel users, kecuali exclude_user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    if exclude_user:
        cursor.execute("SELECT username FROM users WHERE username != ?", (exclude_user,))
    else:
        cursor.execute("SELECT username FROM users")
    
    usernames = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usernames

def send_message(sender, recipient, msg_type, data, filename=None):
    """Menyimpan pesan terenkripsi ke database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        if isinstance(data, str):
            data_blob = data.encode('utf-8')
        else:
            data_blob = data
            
        cursor.execute(
            """
            INSERT INTO messages (sender_username, recipient_username, message_type, encrypted_data, original_filename)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sender, recipient, msg_type, data_blob, filename)
        )
        conn.commit()
        conn.close()
        return True, "Pesan berhasil terkirim."
    except Exception as e:
        return False, f"Gagal mengirim pesan: {e}"

def get_messages_for_user(username):
    """Mengambil semua pesan untuk (recipient) pengguna."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, sender_username, message_type, original_filename, timestamp FROM messages WHERE recipient_username = ? ORDER BY timestamp DESC",
        (username,)
    )
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_message_by_id_for_user(message_id, username):
    """
    Mengambil data blob pesan, TAPI HANYA jika user adalah penerima.
    Ini untuk keamanan endpoint download.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender_username, message_type, encrypted_data, original_filename FROM messages WHERE id = ? AND recipient_username = ?",
        (message_id, username)
    )
    message = cursor.fetchone()
    conn.close()
    return message