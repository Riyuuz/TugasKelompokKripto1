import streamlit as st
import requests
import io
import os
import datetime
import json

# Import client-side face authentication helper
import client_face_auth

st.set_page_config(
    page_title="AetherSecure - Multi-Layer Crypto Vault",
    page_icon="🛡️",
    layout="wide"
)

# --- ALAMAT API SERVER ---
API_BASE_URL = "https://chp.fyuko.app"

# --- CSS KUSTOM (Diperbarui untuk tampilan lebih profesional) ---
custom_css = """
<style>
    /* --- Base --- */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
        background-color: #0F1A2A; /* Dark blue-black */
        color: #F1F5F9; /* Light slate gray text */
    }
    
    /* --- Sidebar --- */
    [data-testid="stSidebar"] {
        background-color: #1E293B; /* Slightly lighter dark blue */
        border-right: 1px solid #334155;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] .stRadio > label {
        color: #F1F5F9;
    }

    /* --- Buttons --- */
    [data-testid="stButton"] > button {
        background-color: #3B82F6; /* Bright Blue */
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 10px 16px;
        transition: background-color 0.3s ease;
        font-weight: 600;
    }
    [data-testid="stButton"] > button:hover {
        background-color: #2563EB; /* Darker Blue */
    }
    [data-testid="stButton"] > button:disabled {
        background-color: #334155;
        color: #94A3B8;
    }
    /* Khusus tombol logout di sidebar (Primary) */
    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"] {
        background-color: #DC2626; /* Red for logout */
    }
    [data-testid="stSidebar"] [data-testid="stButton"] > button[kind="primary"]:hover {
        background-color: #B91C1C;
    }

    /* --- Form & Input Elements --- */
    [data-testid="stForm"] {
        background-color: #1E293B; /* Darker component background */
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
    }
    
    /* Kontainer kustom untuk card layout */
    .st-emotion-cache-1r6slb0 { /* Ini adalah selector untuk st.container(border=True) */
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px !important;
    }
    
    [data-testid="stTextInput"] input, 
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        background-color: #0F1A2A; /* Match main background */
        color: #F1F5F9;
        border: 1px solid #334155;
        border-radius: 8px;
    }
    [data-testid="stTextInput"] input:focus, 
    [data-testid="stTextArea"] textarea:focus,
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within {
        border-color: #3B82F6; /* Highlight blue on focus */
        box-shadow: 0 0 0 2px #3B82F660;
    }

    /* --- Tabs --- */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        border-bottom: 2px solid #334155;
    }
    [data-testid="stTabs"] button[role="tab"] {
        background-color: transparent;
        color: #94A3B8; /* Muted tab text */
        border-radius: 8px 8px 0 0;
        padding: 10px 16px;
    }
    [data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        background-color: #1E293B; /* Active tab background */
        color: #FFFFFF;
        border-bottom: 2px solid #3B82F6; /* Active tab underline */
    }

    /* --- Headers & Text --- */
    h1, h2, h3, h4, h5 {
        color: #FFFFFF;
        font-weight: 600;
    }
    
    /* --- Expander --- */
    [data-testid="stExpander"] summary {
        border: 1px solid #334155;
        border-radius: 8px;
        background-color: #1E293B;
    }
    
    /* --- Status Messages --- */
    [data-testid="stAlert"] {
        border-radius: 8px;
        border: none;
        padding: 16px;
    }
    [data-testid="stAlert"][data-baseweb="alert-negative"] {
        background-color: #EF444430; /* Red tint */
        color: #F87171;
    }
    [data-testid="stAlert"][data-baseweb="alert-positive"] {
        background-color: #10B98130; /* Green tint */
        color: #34D399;
    }
    [data-testid="stAlert"][data-baseweb="alert-info"] {
        background-color: #3B82F630; /* Blue tint */
        color: #60A5FA;
    }
    [data-testid="stAlert"][data-baseweb="alert-warning"] {
        background-color: #F59E0B30; /* Yellow tint */
        color: #FBBF24;
    }

    /* --- Code Block --- */
    [data-testid="stCodeBlock"] code {
        background-color: #1E293B;
        color: #E2E8F0;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 12px;
    }
    
    /* --- Camera Input --- */
    [data-testid="stCameraInput"] video {
        border-radius: 8px;
    }

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- Variabel Sesi ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'access_token' not in st.session_state:
    st.session_state['access_token'] = None
if 'face_encoding_json' not in st.session_state: # Disimpan untuk verifikasi
    st.session_state['face_encoding_json'] = None
    
if 'login_step' not in st.session_state:
    st.session_state['login_step'] = 1
if 'register_step' not in st.session_state:
    st.session_state['register_step'] = 1
if 'reg_username' not in st.session_state:
    st.session_state['reg_username'] = ""
if 'reg_password' not in st.session_state:
    st.session_state['reg_password'] = ""

if 'page' not in st.session_state:
    st.session_state['page'] = "Crypto Tools"
if 'selected_message_id' not in st.session_state:
    st.session_state['selected_message_id'] = None
if 'current_message_blob' not in st.session_state:
    st.session_state['current_message_blob'] = None

# --- Bagian 1: Fungsi Tampilan Login & Logout (Diperbarui) ---

def login_form():
    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<h1 style='text-align: center;'>AetherSecure</h1>", unsafe_allow_html=True)
        
        st.markdown("<h4 style='text-align: center; color: #94A3B8;'>Multi-Layer Crypto Vault</h4>", unsafe_allow_html=True)
        st.empty()
        
        tab_login, tab_register = st.tabs(["🔒 Login", "✍️ Registrasi Pengguna Baru"])
        
        with tab_login:
            if st.session_state['login_step'] == 1:
                st.markdown("##### Masukkan Username dan Password")
                with st.form("login_form_credentials"):
                    username = st.text_input("Username", placeholder="Masukkan username Anda")
                    password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
                    step1_button = st.form_submit_button("Verifikasi Password", use_container_width=True, type="primary")
                    
                    if step1_button:
                        if not username or not password:
                            st.error("Username dan Password tidak boleh kosong.", icon="🚨")
                        else:
                            with st.spinner("Memverifikasi password ke server..."):
                                try:
                                    # 1. Panggil /token untuk verifikasi password
                                    response = requests.post(
                                        f"{API_BASE_URL}/token",
                                        data={"username": username, "password": password}
                                    )
                                    if response.status_code == 200:
                                        token_data = response.json()
                                        temp_token = token_data['access_token']
                                        
                                        # 2. Panggil /users/me untuk mengambil data wajah
                                        headers = {"Authorization": f"Bearer {temp_token}"}
                                        user_data_resp = requests.get(f"{API_BASE_URL}/users/me", headers=headers)
                                        
                                        if user_data_resp.status_code == 200:
                                            user_data = user_data_resp.json()
                                            st.session_state['access_token'] = temp_token
                                            st.session_state['username'] = user_data['username']
                                            st.session_state['face_encoding_json'] = user_data['face_encoding_json']
                                            st.session_state['login_step'] = 2
                                            st.success("Password benar. Lanjut ke verifikasi wajah.", icon="✅")
                                            st.rerun()
                                        else:
                                            st.error("Gagal mengambil data pengguna setelah login.", icon="🚨")
                                    else:
                                        st.error("Login Gagal: Username atau Password salah.", icon="🚨")
                                except requests.ConnectionError:
                                    st.error("Gagal terhubung ke API server.", icon="🌐")

            elif st.session_state['login_step'] == 2:
                st.markdown(f"##### Verifikasi Wajah")
                st.info(f"Halo, **{st.session_state['username']}**. Ambil foto untuk membuka vault.", icon="👤")
                login_face_image = st.camera_input("Ambil foto untuk verifikasi login", key="login_cam")
                
                if login_face_image:
                    with st.spinner("Memverifikasi wajah (secara lokal)..."):
                        # Panggil fungsi verifikasi LOKAL
                        is_match, message = client_face_auth.compare_faces(
                            st.session_state['face_encoding_json'], 
                            login_face_image
                        )
                    
                    if is_match:
                        st.success(f"Login Berhasil! Wajah cocok. Selamat datang.", icon="✅")
                        st.session_state['logged_in'] = True
                        st.session_state['login_step'] = 1 # Reset
                        st.session_state['page'] = "Crypto Tools"
                        st.rerun() 
                    else:
                        st.error(f"Verifikasi Wajah Gagal: {message}. Silakan coba lagi.", icon="❌")

                if st.button("Kembali (Batal Login)", use_container_width=True):
                    # Logout parsial
                    st.session_state['login_step'] = 1
                    st.session_state['username'] = None
                    st.session_state['access_token'] = None
                    st.session_state['face_encoding_json'] = None
                    st.rerun()

        with tab_register:
            st.info("Wajah Anda akan diproses di browser dan encoding-nya akan dikirim ke server.", icon="ℹ️")
            if st.session_state['register_step'] == 1:
                with st.form("register_form_credentials"):
                    st.markdown("##### Langkah 1: Buat Akun Baru")
                    new_username = st.text_input("Username Baru", placeholder="Pilih username unik")
                    new_password = st.text_input("Password Baru", type="password", placeholder="Minimal 8 karakter")
                    confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
                    step1_reg_button = st.form_submit_button("Lanjut ke Registrasi Wajah 📸", use_container_width=True)
                    if step1_reg_button:
                        if not new_username or not new_password:
                            st.warning("Username dan Password tidak boleh kosong.", icon="⚠️")
                        elif new_password != confirm_password:
                            st.warning("Password konfirmasi tidak cocok.", icon="⚠️")
                        else:
                            st.session_state['reg_username'] = new_username
                            st.session_state['reg_password'] = new_password
                            st.session_state['register_step'] = 2
                            st.rerun()
                            
            elif st.session_state['register_step'] == 2:
                st.markdown(f"##### Langkah 2: Registrasi Wajah untuk **{st.session_state['reg_username']}**")
                st.warning("Pastikan wajah Anda terlihat jelas.", icon="⚠️")
                register_face_image = st.camera_input("Ambil foto untuk registrasi biometrik", key="reg_cam")
                
                if register_face_image:
                    if st.button("Daftar 👤", use_container_width=True, type="primary"):
                        with st.spinner("Memproses gambar wajah (secara lokal)..."):
                            # Panggil fungsi encoding LOKAL
                            encoding, message = client_face_auth.get_face_encoding(register_face_image)
                        
                        if encoding is not None:
                            face_encoding_json = json.dumps(encoding.tolist())
                            with st.spinner("Mengirim data registrasi ke server..."):
                                try:
                                    payload = {
                                        "username": st.session_state['reg_username'],
                                        "password": st.session_state['reg_password'],
                                        "face_encoding_json": face_encoding_json
                                    }
                                    response = requests.post(f"{API_BASE_URL}/register", json=payload)
                                    
                                    if response.status_code == 200:
                                        st.success(f"Pengguna '{st.session_state['reg_username']}' berhasil dibuat! Silakan login.", icon="✅")
                                        st.session_state['register_step'] = 1
                                        st.session_state['reg_username'] = ""
                                        st.session_state['reg_password'] = ""
                                    else:
                                        st.error(f"Registrasi Gagal (Server): {response.json().get('detail', 'Error')}", icon="🚨")
                                except requests.ConnectionError:
                                    st.error("Gagal terhubung ke API server.", icon="🌐")
                        else:
                            st.error(f"Registrasi Gagal (Lokal): {message}. Silakan coba ambil foto lagi.", icon="❌")
                            
                if st.button("Kembali (Ganti Username/Password)", use_container_width=True, key="reg_back"):
                    st.session_state['register_step'] = 1
                    st.session_state['reg_username'] = ""
                    st.session_state['reg_password'] = ""
                    st.rerun()

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['access_token'] = None
    st.session_state['face_encoding_json'] = None
    st.session_state['login_step'] = 1
    st.session_state['register_step'] = 1
    st.session_state['page'] = "Crypto Tools"
    st.session_state['selected_message_id'] = None
    st.success("Anda telah keluar.", icon="👋")


# --- Bagian 2: Tampilan Konten Utama (API-driven) ---

def get_auth_headers():
    """Helper untuk mendapatkan header otentikasi."""
    token = st.session_state.get('access_token')
    if not token:
        st.error("Sesi Anda telah berakhir. Silakan logout dan login kembali.", icon="🚨")
        return None
    return {"Authorization": f"Bearer {token}"}

def render_crypto_tools_page():
    st.title("🛡️ AetherSecure Crypto Tools", anchor=False)
    headers = get_auth_headers()
    if not headers: return
    
    tab_text, tab_image, tab_file = st.tabs([
        "💬 **Pesan Teks (Super Enkripsi)**", 
        "🖼️ **Gambar (Steganografi)**", 
        "🗄️ **Enkripsi File (AES)**"
    ])

    with tab_text:
        st.header("Super Enkripsi Teks")
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Input 📝")
                mode = st.radio("Pilih Mode Teks", ["Enkripsi", "Dekripsi"], key="text_mode", horizontal=True)
                text_input = st.text_area("Teks Input", height=150, placeholder="Masukkan teks di sini...")
                with st.expander("Pengaturan Kunci 🔑"):
                    caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3)
                    xor_key = st.text_input("XOR Key (Kunci 2)", type="password", placeholder="Masukkan kunci rahasia...")
        
        with col2:
            with st.container(border=True):
                st.subheader("Output 💡")
                if st.button(f"Proses {mode} Teks ⚡", use_container_width=True, type="primary"):
                    if text_input and xor_key:
                        try:
                            if mode == "Enkripsi":
                                with st.spinner("Mengenkripsi teks..."):
                                    payload = {
                                        "plaintext": text_input,
                                        "caesar_shift": caesar_shift,
                                        "xor_key": xor_key
                                    }
                                    response = requests.post(f"{API_BASE_URL}/crypto/text/encrypt", json=payload, headers=headers)
                                    if response.status_code == 200:
                                        st.code(response.json()['ciphertext'], language=None)
                                    else:
                                        st.error(f"Error server: {response.json().get('detail')}", icon="🚨")
                            else:
                                with st.spinner("Mendekripsi teks..."):
                                    payload = {
                                        "base64_ciphertext": text_input,
                                        "caesar_shift": caesar_shift,
                                        "xor_key": xor_key
                                    }
                                    response = requests.post(f"{API_BASE_URL}/crypto/text/decrypt", json=payload, headers=headers)
                                    if response.status_code == 200:
                                        st.text_area("Hasil Dekripsi:", value=response.json()['plaintext'], height=150, disabled=True)
                                    else:
                                        st.error(f"Error server: {response.json().get('detail')}", icon="🚨")
                        except requests.ConnectionError:
                            st.error("Gagal terhubung ke API server.", icon="🌐")
                    else:
                        st.warning("Mohon masukkan Teks dan Kunci XOR.", icon="⚠️")
                else:
                    st.info("Masukkan input dan klik proses.")


    with tab_image:
        st.header("StegoImage Sender")
        mode = st.radio("Pilih Mode Steganografi", ["Sisipkan Pesan 🔽", "Ekstrak Pesan 🔼"], key="image_mode", horizontal=True)
        
        if mode == "Sisipkan Pesan 🔽":
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader("Input 📝")
                    image_file = st.file_uploader("Upload Gambar Penampung (Cover Image)", type=["png"])
                    message_to_hide = st.text_area("Pesan Rahasia", height=150, placeholder="Masukkan pesan rahasia...")
            with col2:
                with st.container(border=True):
                    st.subheader("Output 💡")
                    if st.button("Sisipkan Pesan ke Gambar 🖼️", use_container_width=True, type="primary"):
                        if image_file and message_to_hide:
                            with st.spinner("Mengirim gambar ke server untuk diproses..."):
                                files = {"image": (image_file.name, image_file, "image/png")}
                                data = {"message": message_to_hide}
                                try:
                                    response = requests.post(f"{API_BASE_URL}/crypto/image/hide", files=files, data=data, headers=headers)
                                    if response.status_code == 200:
                                        st.image(response.content, caption="Gambar Stego (Hasil)")
                                        st.download_button(label="Download Gambar Stego (PNG) 💾", data=response.content, file_name="stego_image.png", mime="image/png", use_container_width=True)
                                    else:
                                        st.error(f"Error server: {response.json().get('detail')}", icon="🚨")
                                except requests.ConnectionError:
                                    st.error("Gagal terhubung ke API server.", icon="🌐")
                        else:
                            st.warning("Mohon upload gambar PNG dan isi pesan rahasia.", icon="⚠️")
                    else:
                        st.info("Upload gambar PNG dan isi pesan untuk disisipkan.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                with st.container(border=True):
                    st.subheader("Input 📝")
                    stego_image_file = st.file_uploader("Upload Gambar Stego (PNG)", type=["png"])
            with col2:
                with st.container(border=True):
                    st.subheader("Output 💡")
                    if st.button("Ekstrak Pesan dari Gambar 🔍", use_container_width=True, type="primary"):
                        if stego_image_file:
                            with st.spinner("Mengirim gambar ke server untuk ekstraksi..."):
                                files = {"image": (stego_image_file.name, stego_image_file, "image/png")}
                                try:
                                    response = requests.post(f"{API_BASE_URL}/crypto/image/extract", files=files, headers=headers)
                                    if response.status_code == 200:
                                        st.text_area("Pesan Rahasia Ditemukan:", value=response.json()['message'], height=150, disabled=True)
                                    else:
                                        st.error(f"Error server: {response.json().get('detail')}", icon="🚨")
                                except requests.ConnectionError:
                                    st.error("Gagal terhubung ke API server.", icon="🌐")
                        else:
                            st.warning("Mohon upload gambar stego PNG.", icon="⚠️")
                    else:
                        st.info("Upload gambar stego untuk mengekstrak pesan.")

    with tab_file:
        st.header("CryptoVault File Security")
        mode = st.radio("Pilih Mode File", ["Enkripsi File 🔒", "Dekripsi File 🔓"], key="file_mode", horizontal=True)
        col1, col2 = st.columns(2)
        with col1:
            with st.container(border=True):
                st.subheader("Input 📝")
                file_to_process = st.file_uploader("Upload File", type=None)
                file_key = st.text_input("Password File", type="password", key="file_key", placeholder="Masukkan password file...")
        with col2:
            with st.container(border=True):
                st.subheader("Output 💡")
                if st.button(f"Proses {mode} ⚡", use_container_width=True, type="primary"):
                    if file_to_process and file_key:
                        with st.spinner(f"Mengirim file ke server untuk {mode}..."):
                            files = {"file": (file_to_process.name, file_to_process, file_to_process.type)}
                            data = {"password": file_key}
                            endpoint = "encrypt" if mode == "Enkripsi File 🔒" else "decrypt"
                            try:
                                response = requests.post(f"{API_BASE_URL}/crypto/file/{endpoint}", files=files, data=data, headers=headers)
                                if response.status_code == 200:
                                    cd = response.headers.get("Content-Disposition", "")
                                    new_filename = cd.split("filename=")[-1].strip('"') if "filename=" in cd else "processed_file"
                                    st.success("Proses file berhasil!", icon="✅")
                                    st.download_button(label=f"Download File Hasil ({new_filename}) 💾", data=response.content, file_name=new_filename, mime="application/octet-stream", use_container_width=True)
                                else:
                                    st.error(f"Error server: {response.json().get('detail')}", icon="🚨")
                            except requests.ConnectionError:
                                st.error("Gagal terhubung ke API server.", icon="🌐")
                else:
                    st.warning("Mohon upload file dan masukkan password.", icon="⚠️")

def render_messaging_page():
    st.title("📨 Pesan Aman Terenkripsi", anchor=False)
    headers = get_auth_headers()
    if not headers: return
    
    tab_inbox, tab_send = st.tabs(["📥 Kotak Masuk", "📬 Kirim Pesan Baru"])
    
    # --- 1. TAB KIRIM PESAN ---
    with tab_send:
        with st.container(border=True):
            st.subheader("Kirim Pesan Terenkripsi Baru")
            
            try:
                response = requests.get(f"{API_BASE_URL}/users", headers=headers)
                if response.status_code == 200:
                    all_users = response.json()
                else:
                    all_users = []
                    st.error("Gagal memuat daftar pengguna.", icon="🚨")
            except requests.ConnectionError:
                all_users = []
                st.error("Gagal terhubung ke server.", icon="🌐")
                
            if not all_users:
                st.warning("Saat ini tidak ada pengguna lain untuk dikirimi pesan.", icon="👥")
                return

            recipient = st.selectbox("Pilih Penerima:", all_users)
            msg_type = st.radio("Pilih Tipe Pesan:", ["Teks Super Enkripsi", "Gambar Steganografi", "File AES"], horizontal=True, key="send_msg_type")
            
            if msg_type == "Teks Super Enkripsi":
                text_input = st.text_area("Teks Plaintext:", placeholder="Ketik pesan rahasia...")
                col1, col2 = st.columns(2)
                with col1:
                    caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3, key="send_caesar")
                with col2:
                    xor_key = st.text_input("XOR Key (Kunci 2)", type="password", key="send_xor", placeholder="Kunci rahasia...")
                
                if st.button("Kirim Pesan Teks 🚀", use_container_width=True, type="primary"):
                    if text_input and xor_key and recipient:
                        with st.spinner("Mengirim pesan teks..."):
                            payload = {
                                "recipient_username": recipient,
                                "plaintext": text_input,
                                "caesar_shift": caesar_shift,
                                "xor_key": xor_key
                            }
                            try:
                                response = requests.post(f"{API_BASE_URL}/messages/send/text", json=payload, headers=headers)
                                if response.status_code == 200:
                                    st.success(f"Pesan terenkripsi berhasil dikirim ke **{recipient}**!", icon="✅")
                                    st.info("PENTING: Beri tahu penerima kunci/password Anda.", icon="🔑")
                                else:
                                    st.error(f"Gagal mengirim: {response.json().get('detail')}", icon="🚨")
                            except requests.ConnectionError:
                                st.error("Gagal terhubung ke server.", icon="🌐")
                    else:
                        st.warning("Mohon lengkapi semua field.", icon="⚠️")
                        
            elif msg_type == "Gambar Steganografi":
                image_file = st.file_uploader("Upload Gambar Penampung", type=["png"], key="send_stego_img")
                message_to_hide = st.text_area("Pesan Rahasia untuk Disisipkan:", placeholder="Ketik pesan rahasia...")
                
                if st.button("Kirim Pesan Gambar 🚀", use_container_width=True, type="primary"):
                    if image_file and message_to_hide and recipient:
                        with st.spinner("Mengirim gambar stego..."):
                            files = {"image": (image_file.name, image_file, "image/png")}
                            data = {"recipient": recipient, "message": message_to_hide}
                            try:
                                response = requests.post(f"{API_BASE_URL}/messages/send/stego", files=files, data=data, headers=headers)
                                if response.status_code == 200:
                                    st.success(f"Gambar stego berhasil dikirim ke **{recipient}**!", icon="✅")
                                else:
                                    st.error(f"Gagal mengirim: {response.json().get('detail')}", icon="🚨")
                            except requests.ConnectionError:
                                st.error("Gagal terhubung ke server.", icon="🌐")
                    else:
                        st.warning("Mohon lengkapi semua field.", icon="⚠️")
                                
            elif msg_type == "File AES":
                file_to_process = st.file_uploader("Upload File untuk Dienkripsi", type=None, key="send_aes_file")
                file_key = st.text_input("Password File AES", type="password", key="send_aes_key", placeholder="Password rahasia file...")

                if st.button("Kirim File AES 🚀", use_container_width=True, type="primary"):
                    if file_to_process and file_key and recipient:
                        with st.spinner("Mengirim file terenkripsi..."):
                            files = {"file": (file_to_process.name, file_to_process, file_to_process.type)}
                            data = {"recipient": recipient, "password": file_key}
                            try:
                                response = requests.post(f"{API_BASE_URL}/messages/send/aes", files=files, data=data, headers=headers)
                                if response.status_code == 200:
                                    st.success(f"File AES berhasil dikirim ke **{recipient}**!", icon="✅")
                                    st.info("PENTING: Beri tahu penerima password file Anda.", icon="🔑")
                                else:
                                    st.error(f"Gagal mengirim: {response.json().get('detail')}", icon="🚨")
                            except requests.ConnectionError:
                                st.error("Gagal terhubung ke server.", icon="🌐")
                    else:
                        st.warning("Mohon lengkapi semua field.", icon="⚠️")

    # --- 2. TAB KOTAK MASUK ---
    with tab_inbox:
        st.subheader("Kotak Masuk Anda")
        
        # Tampilkan pesan yang dipilih (jika ada) DI BAGIAN ATAS
        if 'selected_message_id' in st.session_state and st.session_state['selected_message_id'] is not None:
            render_message_detail(st.session_state['selected_message_id'], headers)

        st.divider()
        st.subheader("Daftar Pesan:")
        
        try:
            response = requests.get(f"{API_BASE_URL}/messages/inbox", headers=headers)
            if response.status_code == 200:
                my_messages = response.json()
            else:
                my_messages = []
                st.error("Gagal memuat kotak masuk.", icon="🚨")
        except requests.ConnectionError:
            my_messages = []
            st.error("Gagal terhubung ke server.", icon="🌐")

        if not my_messages:
            st.info("Anda belum memiliki pesan masuk.", icon="📩")
            return

        for msg in my_messages:
            msg_id = msg['id']
            if msg_id == st.session_state.get('selected_message_id'):
                continue # Jangan tampilkan jika sedang dibuka
            
            ts = datetime.datetime.strptime(msg['timestamp'], '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %H:%M')
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.5])
                with col1:
                    sender = msg['sender_username']
                    if sender is None:
                        display_sender = "_[Pengguna Dihapus]_"
                    else:
                        display_sender = f"`{sender}`"
                    st.markdown(f"**Dari:** {display_sender}")
                    st.caption(f"Diterima: {ts}")
                with col2:
                    st.markdown(f"**Tipe:**")
                    st.caption(f"{msg['message_type']}")
                with col3:
                    st.button("Buka & Dekripsi 🔑", key=f"open_{msg_id}", use_container_width=True, on_click=lambda mid=msg_id: st.session_state.update(selected_message_id=mid, current_message_blob=None))

def render_message_detail(message_id, headers):
    """Menampilkan UI dekripsi untuk pesan yang dipilih."""
    
    with st.container(border=True):
        st.subheader(f"Membuka Pesan #{message_id}")
        
        # Step 1: Muat data blob jika belum ada
        if st.session_state.get('current_message_blob') is None:
            if st.button("Muat Data Pesan Terenkripsi 📥", use_container_width=True, type="primary"):
                with st.spinner("Mengunduh data pesan..."):
                    try:
                        response = requests.get(f"{API_BASE_URL}/messages/{message_id}/data", headers=headers)
                        if response.status_code == 200:
                            st.session_state['current_message_blob'] = response.content
                            st.session_state['current_message_type'] = response.headers.get('Content-Type', 'application/octet-stream')
                            st.session_state['current_message_filename'] = response.headers.get("Content-Disposition", "filename=file").split("filename=")[-1].strip('"')
                            st.rerun()
                        else:
                            st.error(f"Gagal memuat pesan: {response.json().get('detail')}", icon="🚨")
                            st.session_state['selected_message_id'] = None
                    except requests.ConnectionError:
                        st.error("Gagal terhubung ke server.", icon="🌐")
            
            if st.button("Tutup Pesan Ini 🔼", use_container_width=True):
                st.session_state['selected_message_id'] = None
                st.session_state['current_message_blob'] = None
                st.rerun()
            return # Hentikan di sini sampai data dimuat

        # Step 2: Data telah dimuat, tampilkan UI dekripsi
        
        msg_blob = st.session_state['current_message_blob']
        msg_filename = st.session_state['current_message_filename']
        st.info(f"Data terenkripsi **{msg_filename}** telah dimuat. Silakan masukkan kunci.", icon="ℹ️")
        
        # Tentukan tipe berdasarkan nama file (asumsi dari server)
        if msg_filename.endswith(".txt"): # Teks Super Enkripsi
            col1, col2 = st.columns(2)
            with col1:
                caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3, key="decrypt_caesar")
            with col2:
                xor_key = st.text_input("XOR Key (Kunci 2)", type="password", key="decrypt_xor", placeholder="Kunci rahasia...")
            
            if st.button("Dekripsi Teks ⚡", use_container_width=True, type="primary"):
                if xor_key:
                    try:
                        base64_ciphertext = msg_blob.decode('utf-8')
                        payload = {
                            "base64_ciphertext": base64_ciphertext,
                            "caesar_shift": caesar_shift,
                            "xor_key": xor_key
                        }
                        response = requests.post(f"{API_BASE_URL}/crypto/text/decrypt", json=payload, headers=headers)
                        if response.status_code == 200:
                            st.success("Dekripsi berhasil!", icon="✅")
                            st.text_area("Hasil Dekripsi:", value=response.json()['plaintext'], height=150, disabled=True)
                        else:
                            st.error(f"Gagal mendekripsi: {response.json().get('detail')}", icon="🚨")
                    except Exception as e:
                        st.error(f"Error: {e}", icon="🚨")
                else:
                    st.warning("Mohon masukkan Kunci XOR.", icon="⚠️")

        elif msg_filename.startswith("stego_"): # Gambar Steganografi
            st.info("Ini adalah file gambar stego. Download dan buka di tab 'Crypto Tools' > 'Gambar' > 'Ekstrak Pesan' untuk membacanya.", icon="🖼️")
            st.download_button(
                label=f"Download Gambar Stego ({msg_filename}) 💾",
                data=msg_blob,
                file_name=msg_filename,
                mime="image/png",
                use_container_width=True
            )

        elif msg_filename.endswith(".enc"): # File AES
            file_key = st.text_input("Password File AES", type="password", key="decrypt_aes_key", placeholder="Password rahasia file...")
            if st.button("Dekripsi File ⚡", use_container_width=True, type="primary"):
                if file_key:
                    with st.spinner("Mengirim file ke server untuk dekripsi..."):
                        files = {"file": (msg_filename, msg_blob, "application/octet-stream")}
                        data = {"password": file_key}
                        try:
                            response = requests.post(f"{API_BASE_URL}/crypto/file/decrypt", files=files, data=data, headers=headers)
                            if response.status_code == 200:
                                new_filename = response.headers.get("Content-Disposition", "filename=decrypted_file").split("filename=")[-1].strip('"')
                                st.success("File berhasil didekripsi!", icon="✅")
                                st.download_button(
                                    label=f"Download File Asli ({new_filename}) 💾",
                                    data=response.content,
                                    file_name=new_filename,
                                    mime="application/octet-stream",
                                    use_container_width=True
                                )
                            else:
                                st.error(f"DEKRIPSI GAGAL: {response.json().get('detail')}", icon="🚨")
                        except requests.ConnectionError:
                            st.error("Gagal terhubung ke server.", icon="🌐")
                else:
                    st.warning("Mohon masukkan password file.", icon="⚠️")
        
        st.divider()
        if st.button("Tutup Pesan Ini 🔼", use_container_width=True):
            st.session_state['selected_message_id'] = None
            st.session_state['current_message_blob'] = None
            st.rerun()


def main_app_content():
    st.sidebar.title(f"Selamat Datang,")
    st.sidebar.markdown(f"<h2 style='color: #FFFFFF; margin-top: -10px;'>{st.session_state['username']}!</h2>", unsafe_allow_html=True)
    
    st.session_state.page = st.sidebar.radio(
        "Menu Navigasi",
        ["🧰 Crypto Tools", "📨 Pesan Aman"],
        key="nav_radio"
    )
    
    st.sidebar.button("Logout 🚪", on_click=logout, use_container_width=True, type="primary")
    st.sidebar.divider()
    st.sidebar.header("Tentang Aplikasi")
    st.sidebar.info("AetherSecure (Client-Server) adalah vault kriptografi berlapis untuk mengamankan data Anda.")
    st.sidebar.divider()
    with st.sidebar.expander("Zona Berbahaya ⚠️"):
        st.warning("Menghapus akun Anda bersifat permanen dan tidak dapat dibatalkan.") 
        password_confirm = st.text_input(
            "Konfirmasi password Anda untuk menghapus:", 
            type="password",
            key="delete_confirm_pass"
            )
            
        if st.button("Hapus Akun Saya Secara Permanen", use_container_width=True):
            if password_confirm:
                headers = get_auth_headers()
                if headers:
                    try:
                        # Panggil endpoint DELETE baru
                        response = requests.delete(
                            f"{API_BASE_URL}/users/me",
                            json={"password": password_confirm}, # Kirim password di body
                            headers=headers
                            )
                            
                        if response.status_code == 200:
                            st.success("Akun Anda telah berhasil dihapus.")
                            st.balloons()
                            # Panggil logout untuk membersihkan sesi
                            logout()
                            st.rerun() # Rerun untuk kembali ke layar login
                        else:
                            st.error(f"Gagal: {response.json().get('detail')}", icon="🚨")
                    except requests.ConnectionError:
                        st.error("Gagal terhubung ke server.", icon="🌐")
                else:
                    st.error("Masukkan password Anda untuk konfirmasi.", icon="🔒")
    st.sidebar.divider()
    
    if st.session_state.page == "🧰 Crypto Tools":
        render_crypto_tools_page()
    elif st.session_state.page == "📨 Pesan Aman":
        render_messaging_page()
    

# --- Bagian 3: Logika Utama (Menampilkan Login atau Konten Aplikasi) ---
if st.session_state['logged_in']:
    main_app_content()
else:
    login_form()