# client_face_auth.py
import cv2
import numpy as np
import json
import streamlit as st
import io

# --- 1. DEFINISI DAN PEMUATAN MODEL OpenCV (DNN) ---
# Pastikan file-file ini ada di dalam folder 'models'
DETECTOR_PROTO = 'models/deploy.prototxt'
DETECTOR_MODEL = 'models/res10_300x300_ssd_iter_140000.caffemodel'
ENCODER_MODEL = 'models/openface.nn4.small2.v1.t7'

@st.cache_resource
def load_models():
    """Memuat model DNN menggunakan cache Streamlit."""
    print("Loading DNN models...")
    try:
        detector_net = cv2.dnn.readNetFromCaffe(DETECTOR_PROTO, DETECTOR_MODEL)
        encoder_net = cv2.dnn.readNetFromTorch(ENCODER_MODEL)
        return detector_net, encoder_net
    except cv2.error as e:
        st.error(f"Error: Gagal memuat model DNN. Pastikan file model ada di folder 'models'. Error: {e}")
        return None, None

def get_face_encoding(image_file):
    """
    Mendapatkan encoding wajah (vektor 128-dimensi) dari file gambar
    menggunakan OpenCV DNN.
    `image_file` adalah objek seperti file (mis: BytesIO, st.camera_input).
    """
    detector_net, encoder_net = load_models()
    if detector_net is None or encoder_net is None:
        print("Model DNN tidak dimuat.")
        return None, "Model DNN tidak dimuat."
    
    try:
        # Baca gambar dari memory (dari st.camera_input)
        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if image is None:
            return None, "Gagal membaca format gambar."
            
        (h, w) = image.shape[:2]
        
        # 1. Deteksi Wajah
        blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0),
                                     swapRB=False, crop=False)
        
        detector_net.setInput(blob)
        detections = detector_net.forward()
        if len(detections) == 0:
            return None, "Tidak ada wajah yang terdeteksi."
            
        best_detection_index = np.argmax(detections[0, 0, :, 2])
        confidence = detections[0, 0, best_detection_index, 2]
        
        if confidence < 0.7: # Threshold kepercayaan
            return None, "Wajah tidak cukup jelas."
            
        box = detections[0, 0, best_detection_index, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        face = image[startY:endY, startX:endX]
        
        if face.shape[0] < 20 or face.shape[1] < 20:
            return None, "Wajah yang terdeteksi terlalu kecil."
            
        # 2. Enkoding Wajah
        face_blob = cv2.dnn.blobFromImage(face, 1.0 / 255, (96, 96),
                                         (0, 0, 0), swapRB=True, crop=True)
        
        encoder_net.setInput(face_blob)
        encoding = encoder_net.forward()
        return encoding.flatten(), "Encoding berhasil." # Flatten menjadi 1D vector
        
    except Exception as e:
        print(f"Error saat memproses gambar OpenCV: {e}")
        return None, f"Error internal: {e}"

def compare_faces(known_encoding_json, new_image_file):
    """
    Membandingkan wajah baru dengan encoding yang tersimpan (JSON string).
    Semua proses terjadi di client.
    """
    try:
        known_encoding = np.array(json.loads(known_encoding_json))
        
        # Pastikan file pointer di awal
        new_image_file.seek(0)
        new_encoding, message = get_face_encoding(new_image_file)
        
        if new_encoding is not None:
            dot_product = np.dot(known_encoding, new_encoding)
            norm_known = np.linalg.norm(known_encoding)
            norm_new = np.linalg.norm(new_encoding)
            
            if norm_known == 0 or norm_new == 0:
                return False, "Error normalisasi encoding."
                
            cosine_similarity = dot_product / (norm_known * norm_new)
            threshold = 0.80 
            print(f"Cosine Similarity: {cosine_similarity}")
            
            if cosine_similarity > threshold:
                return True, "Wajah cocok."
            else:
                return False, "Wajah tidak cocok."
        else:
            return False, message # Kembalikan pesan error dari get_face_encoding
            
    except Exception as e:
        print(f"Error saat membandingkan wajah: {e}")
        return False, f"Error perbandingan: {e}"