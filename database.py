# database.py
import sqlite3
import bcrypt
import cv2
import numpy as np
import json
import io
import datetime  # <-- Ditambahkan

DATABASE_FILE = 'users.db'

# --- 1. DEFINISI DAN PEMUATAN MODEL OpenCV (DNN) ---
# Pastikan file-file ini ada di dalam folder 'models'
DETECTOR_PROTO = 'models/deploy.prototxt'
DETECTOR_MODEL = 'models/res10_300x300_ssd_iter_140000.caffemodel'
ENCODER_MODEL = 'models/openface.nn4.small2.v1.t7'

# Coba muat model saat skrip dimulai.
try:
    detector_net = cv2.dnn.readNetFromCaffe(DETECTOR_PROTO, DETECTOR_MODEL)
    encoder_net = cv2.dnn.readNetFromTorch(ENCODER_MODEL)
except cv2.error as e:
    print(f"Error: Gagal memuat model DNN. Pastikan file model ada di folder 'models'. Error: {e}")
    detector_net = None
    encoder_net = None

# --- 2. Fungsi Hashing Password (Tetap Sama) ---
def hash_password_bcrypt(password):
    """Menghasilkan hash bcrypt untuk password."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password_bcrypt(password, stored_hash):
    """Memverifikasi password dengan hash yang tersimpan."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        return False

# --- 3. Fungsi Biometrik (Tetap Sama) ---
def get_face_encoding(image_file):
    """Mendapatkan encoding wajah (vektor 128-dimensi) dari file gambar menggunakan OpenCV DNN."""
    if detector_net is None or encoder_net is None:
        print("Model DNN tidak dimuat.")
        return None
    try:
        # Baca gambar dari memory (dari st.camera_input)
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        (h, w) = image.shape[:2]
        
        # 1. Deteksi Wajah
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0),
                                     swapRB=False, crop=False)
        
        detector_net.setInput(blob)
        detections = detector_net.forward()
        if len(detections) == 0:
            return None # Tidak ada wajah
            
        best_detection_index = np.argmax(detections[0, 0, :, 2])
        confidence = detections[0, 0, best_detection_index, 2]
        
        if confidence < 0.7: # Threshold kepercayaan
            return None # Wajah tidak cukup jelas
            
        box = detections[0, 0, best_detection_index, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        face = image[startY:endY, startX:endX]
        
        if face.shape[0] < 20 or face.shape[1] < 20:
            return None
            
        # 2. Enkoding Wajah
        face_blob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96),
                                         (0, 0, 0), swapRB=True, crop=True)
        
        encoder_net.setInput(face_blob)
        encoding = encoder_net.forward()
        return encoding.flatten() # Flatten menjadi 1D vector
        
    except Exception as e:
        print(f"Error saat memproses gambar OpenCV: {e}")
        return None

def compare_faces(known_encoding_json, new_image_file):
    """Membandingkan wajah baru dengan encoding yang tersimpan menggunakan Jarak Kosinus."""
    try:
        known_encoding = np.array(json.loads(known_encoding_json))
        new_encoding = get_face_encoding(new_image_file)
        
        if new_encoding is not None:
            dot_product = np.dot(known_encoding, new_encoding)
            norm_known = np.linalg.norm(known_encoding)
            norm_new = np.linalg.norm(new_encoding)
            
            if norm_known == 0 or norm_new == 0:
                return False
                
            cosine_similarity = dot_product / (norm_known * norm_new)
            threshold = 0.80 
            print(f"Cosine Similarity: {cosine_similarity}")
            return cosine_similarity > threshold
        else:
            return False
            
    except Exception as e:
        print(f"Error saat membandingkan wajah: {e}")
        return False

# --- 4. Fungsi Database (Diperbarui) ---

def init_db():
    """Membuat tabel users DAN messages."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Tabel Users (Tetap Sama)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        face_encoding_json TEXT
    );
    ''')
    
    # --- TABEL BARU UNTUK PESAN ---
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
    # --- AKHIR TABEL BARU ---
    
    conn.commit()
    conn.close()
    print("Database 'users.db' dan 'messages.db' berhasil diinisialisasi.")

# Fungsi add_user (Tetap Sama)
def add_user(username, password, face_image_file):
    """Menambahkan pengguna baru ke database dengan password HASH dan FACE ENCODING."""
    if not username or not password or not face_image_file:
        return False, "Data tidak lengkap."
    try:
        face_encoding = get_face_encoding(face_image_file)
        if face_encoding is None:
            return False, "Tidak ada wajah yang terdeteksi di gambar. Coba lagi."

        face_encoding_json = json.dumps(face_encoding.tolist())
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

# Fungsi verify_user (Tetap Sama)
def verify_user(username, password, face_image_file):
    """Memverifikasi login pengguna (Password DAN Wajah)."""
    if not username or not password or not face_image_file:
        return False, "Data login tidak lengkap."
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash, face_encoding_json FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    
    if result:
        stored_hash, stored_face_encoding_json = result[0], result[1]
        if not verify_password_bcrypt(password, stored_hash):
            conn.close()
            return False, "Password salah."
        if not compare_faces(stored_face_encoding_json, face_image_file):
            conn.close()
            return False, "Wajah tidak cocok dengan data yang tersimpan."
        conn.close()
        return True, "Login berhasil."
    conn.close()
    return False, "Username tidak ditemukan."

# --- 5. FUNGSI-FUNGSI BARU UNTUK FITUR PESAN ---

def get_all_usernames(exclude_user=None):
    """Mengambil semua username dari tabel users, kecuali exclude_user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    if exclude_user:
        cursor.execute("SELECT username FROM users WHERE username != ?", (exclude_user,))
    else:
        cursor.execute("SELECT username FROM users")
    
    # Ubah format hasil dari [(user1,), (user2,)] menjadi [user1, user2]
    usernames = [row[0] for row in cursor.fetchall()]
    conn.close()
    return usernames

def send_message(sender, recipient, msg_type, data, filename=None):
    """Menyimpan pesan terenkripsi ke database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        # Simpan data sebagai BLOB (biner)
        # Jika data adalah string (misal Base64), ubah ke bytes
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
    # --- BARU: Menggunakan row_factory untuk hasil seperti dictionary ---
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, sender_username, message_type, original_filename, timestamp FROM messages WHERE recipient_username = ? ORDER BY timestamp DESC",
        (username,)
    )
    # Ubah hasil (sqlite3.Row) menjadi dictionary standar
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_message_by_id(message_id):
    """Mengambil satu pesan spesifik (termasuk datanya) berdasarkan ID."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sender_username, message_type, encrypted_data, original_filename FROM messages WHERE id = ?",
        (message_id,)
    )
    message = cursor.fetchone()
    conn.close()
    return message

