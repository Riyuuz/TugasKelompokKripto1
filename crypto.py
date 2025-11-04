import bcrypt
import base64
import io
from PIL import Image
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.backends import default_backend
import os

# --- 1. Login (Bcrypt Hashing) ---

def hash_password_bcrypt(password):
    """Menghasilkan hash bcrypt untuk password baru."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def verify_password_bcrypt(password, stored_hash):
    """Memverifikasi password yang dimasukkan dengan hash yang tersimpan."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
    except ValueError:
        return False

# --- 2. Super Enkripsi Teks (Caesar + XOR) ---

def encrypt_caesar(text, shift):
    """Enkripsi menggunakan Caesar Cipher (hanya huruf alfabet)."""
    result = ""
    for char in text:
        if 'a' <= char <= 'z':
            shifted_char = chr(((ord(char) - ord('a') + shift) % 26) + ord('a'))
        elif 'A' <= char <= 'Z':
            shifted_char = chr(((ord(char) - ord('A') + shift) % 26) + ord('A'))
        else:
            shifted_char = char
        result += shifted_char
    return result

def decrypt_caesar(text, shift):
    """Dekripsi Caesar Cipher."""
    return encrypt_caesar(text, -shift)

def encrypt_decrypt_xor(data_bytes, key):
    """Enkripsi/Dekripsi menggunakan XOR Cipher pada data biner."""
    key_bytes = key.encode('utf-8')
    key_len = len(key_bytes)
    output_bytes = bytearray()
    
    for i in range(len(data_bytes)):
        xor_byte = data_bytes[i] ^ key_bytes[i % key_len]
        output_bytes.append(xor_byte)
        
    return bytes(output_bytes) # Kembalikan sebagai immutable bytes

def super_encrypt_text(plaintext, caesar_shift, xor_key):
    """Super Enkripsi: Caesar -> XOR -> Base64."""
    # 1. Enkripsi Caesar (String -> String)
    caesar_ciphertext = encrypt_caesar(plaintext, caesar_shift)
    
    # 2. Enkripsi XOR (String -> Bytes)
    xor_ciphertext_bytes = encrypt_decrypt_xor(caesar_ciphertext.encode('utf-8'), xor_key)
    
    # 3. Encode ke Base64 (Bytes -> String) untuk ditampilkan
    return base64.b64encode(xor_ciphertext_bytes).decode('utf-8')

def super_decrypt_text(base64_ciphertext, caesar_shift, xor_key):
    """Super Dekripsi: Base64 -> XOR -> Caesar."""
    try:
        # 1. Decode dari Base64 (String -> Bytes)
        xor_ciphertext_bytes = base64.b64decode(base64_ciphertext.encode('utf-8'))
        
        # 2. Dekripsi XOR (Bytes -> Bytes)
        caesar_ciphertext_bytes = encrypt_decrypt_xor(xor_ciphertext_bytes, xor_key)
        
        # 3. Dekripsi Caesar (Bytes -> String)
        plaintext = decrypt_caesar(caesar_ciphertext_bytes.decode('utf-8'), caesar_shift)
        return plaintext
    except Exception as e:
        print(f"Error dekripsi: {e}")
        return "DEKRIPSI GAGAL: Kunci atau format data salah."


# --- 3. Steganografi Gambar (LSB) ---

def text_to_binary(text):
    """Mengubah string teks (ASCII) menjadi string biner."""
    return ''.join(format(ord(char), '08b') for char in text)

def binary_to_text(binary_stream):
    """Mengubah string biner kembali menjadi string teks."""
    text = ""
    for i in range(0, len(binary_stream), 8):
        byte_segment = binary_stream[i:i+8]
        if len(byte_segment) == 8:
            try:
                text += chr(int(byte_segment, 2))
            except ValueError:
                pass # Abaikan jika ada sisa bit yang tidak lengkap
    return text

def stego_hide_message(image_bytes, secret_message):
    """Menyembunyikan pesan rahasia di dalam gambar menggunakan LSB."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        
        # Tambahkan delimiter unik untuk menandai akhir pesan
        secret_message += "::EOF::"
        secret_binary = text_to_binary(secret_message)
        
        data_index = 0
        img_data = list(img.getdata())
        new_img_data = []

        for pixel in img_data:
            if data_index < len(secret_binary):
                new_pixel = []
                # Ubah LSB dari R, G, B
                for i in range(3): # R, G, B
                    if data_index < len(secret_binary):
                        # Ubah LSB piksel
                        new_val = (pixel[i] & 0xFE) | int(secret_binary[data_index])
                        new_pixel.append(new_val)
                        data_index += 1
                    else:
                        new_pixel.append(pixel[i])
                new_img_data.append(tuple(new_pixel))
            else:
                new_img_data.append(pixel) # Salin piksel asli jika pesan sudah selesai

        if data_index < len(secret_binary):
            raise ValueError("Gambar terlalu kecil untuk menyembunyikan pesan ini.")
            
        new_img = Image.new(img.mode, img.size)
        new_img.putdata(new_img_data)
        
        # Simpan gambar baru ke memory
        output_buffer = io.BytesIO()
        new_img.save(output_buffer, format='PNG')
        return output_buffer.getvalue()

    except Exception as e:
        raise ValueError(f"Error steganografi: {e}")


def stego_extract_message(stego_image_bytes):
    """Mengekstrak pesan rahasia dari gambar stego (LSB)."""
    try:
        img = Image.open(io.BytesIO(stego_image_bytes)).convert('RGB')
        binary_stream = ""
        delimiter = "::EOF::"
        delimiter_binary = text_to_binary(delimiter)
        
        img_data = img.getdata()

        for pixel in img_data:
            for i in range(3): # R, G, B
                # Baca LSB (bit terakhir)
                binary_stream += str(pixel[i] & 1)
                
                # Cek jika delimiter ditemukan
                if binary_stream.endswith(delimiter_binary):
                    # Hapus delimiter dari hasil
                    message_binary = binary_stream[:-len(delimiter_binary)]
                    return binary_to_text(message_binary)
        
        return "Pesan tidak ditemukan atau delimiter rusak."
    except Exception as e:
        return f"Error ekstraksi: {e}"


# --- 4. Enkripsi File (AES) ---

def get_aes_key_from_password(password_str, salt):
    """Membuat kunci AES 32-byte dari password menggunakan PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )
    return kdf.derive(password_str.encode('utf-8'))

def aes_encrypt_file(file_bytes, password):
    """Enkripsi file menggunakan AES-256-GCM."""
    try:
        # 1. Hasilkan Salt (untuk KDF) dan Nonce (untuk AES-GCM)
        salt = os.urandom(16)
        nonce = os.urandom(12) # GCM direkomendasikan 12 bytes
        
        # 2. Buat Kunci dari Password
        key = get_aes_key_from_password(password, salt)
        
        # 3. Inisialisasi Cipher AES-GCM
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # 4. Enkripsi Data
        encrypted_data = encryptor.update(file_bytes) + encryptor.finalize()
        
        # 5. Gabungkan: salt + nonce + authentication_tag + encrypted_data
        # Tag (16 bytes) penting untuk verifikasi integritas
        return salt + nonce + encryptor.tag + encrypted_data
        
    except Exception as e:
        raise ValueError(f"Error enkripsi file: {e}")


def aes_decrypt_file(encrypted_file_bytes, password):
    """Dekripsi file AES-256-GCM."""
    try:
        # 1. Ekstrak komponen dari file
        salt = encrypted_file_bytes[0:16]
        nonce = encrypted_file_bytes[16:28]  # 12 bytes
        tag = encrypted_file_bytes[28:44]   # 16 bytes
        encrypted_data = encrypted_file_bytes[44:]
        
        # 2. Buat Ulang Kunci dari Password dan Salt
        key = get_aes_key_from_password(password, salt)
        
        # 3. Inisialisasi Cipher AES-GCM
        cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        
        # 4. Dekripsi Data (akan gagal jika tag atau kunci salah)
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
        return decrypted_data
        
    except Exception as e:
        # Ini akan gagal (InvalidTag) jika password salah
        raise ValueError(f"DEKRIPSI GAGAL. Password salah atau file rusak. Error: {e}")