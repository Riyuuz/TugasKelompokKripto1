import streamlit as st
import crypto  
import database 
import io
import os
import datetime

st.set_page_config(
    page_title="AetherSecure - Multi-Layer Crypto Vault",
    page_icon="🛡️",
    layout="wide"
)

# --- CSS KUSTOM ---
custom_css = """
<style>
    [data-testid="stAppViewContainer"] > .main {
        background-color: #0F1A2A;
        color: #F1F5F9;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #FFFFFF;
    }
    
    [data-testid="stAppViewContainer"] > .main .block-container {
        max-width: 1100px;
        padding-top: 2rem;
    }
    
    [data-testid="stSidebar"] {
        background-color: #1E2A3A;
        border-right: 1px solid #334155;
    }
    
    .stButton > button[kind="primary"] {
        background-color: #42A5F5;
        color: #FFFFFF;
        border: none;
        border-radius: 0.5rem;
        transition: background-color 0.3s ease;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #1E88E5;
        color: #FFFFFF;
    }
    
    .stButton > button:not([kind="primary"]) {
        background-color: #2A3A4A;
        color: #F1F5F9;
        border: 1px solid #334155;
        border-radius: 0.5rem;
        transition: all 0.3s ease;
    }
    .stButton > button:not([kind="primary"]):hover {
        background-color: #334155;
        color: #FFFFFF;
        border-color: #42A5F5;
    }
    .stButton > button:not([kind="primary"]):focus {
        box-shadow: 0 0 0 2px rgba(66, 165, 245, 0.3) !important;
        border-color: #42A5F5 !important;
    }

    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #42A5F5;
        border-bottom-color: #42A5F5;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab-list"] button {
         color: #F1F5F9;
         border-radius: 0.5rem 0.5rem 0 0;
    }

    .stTextInput input, .stTextArea textarea {
        background-color: #2A3A4A;
        color: #F1F5F9;
        border: 1px solid #334155;
        border-radius: 0.5rem;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #42A5F5;
        box-shadow: 0 0 0 2px rgba(66, 165, 245, 0.3);
    }
    [data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background-color: #42A5F5;
    }
    
    [data-testid="stInfo"] {
        background-color: rgba(66, 165, 245, 0.1);
        border: 1px solid rgba(66, 165, 245, 0.2);
        color: #F1F5F9;
        border-radius: 0.5rem;
    }
    [data-testid="stWarning"] {
        background-color: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.2);
        color: #F1F5F9;
        border-radius: 0.5rem;
    }
    [data-testid="stError"] {
        background-color: rgba(220, 38, 38, 0.1);
        border: 1px solid rgba(220, 38, 38, 0.2);
        border-radius: 0.5rem;
    }
    
    [data-testid="stFileUploader"] {
        background-color: #2A3A4A;
        border: 1px dashed #42A5F5;
        border-radius: 0.5rem;
    }
    [data-testid="stFileUploader"] label, [data-testid="stFileUploader"] small {
        color: #F1F5F9;
    }

    [data-testid="stCameraInput"] > div > div {
        background-color: #2A3A4A;
        border-radius: 0.5rem;
    }
    [data-testid="stCameraInput"] span {
        color: #F1F5F9;
    }

    [data-testid="stExpander"] {
        background-color: #2A3A4A;
        border: 1px solid #334155;
        border-radius: 0.5rem;
    }
    [data-testid="stExpander"] summary {
        border-radius: 0.5rem;
    }
    [data-testid="stExpander"] summary > span {
        color: #FFFFFF;
    }
    [data-testid="stExpander"] summary svg {
        fill: #FFFFFF;
    }

    [data-testid="stCodeBlock"] {
        background-color: #1E2A3A;
        border: 1px solid #334155;
        border-radius: 0.5rem;
    }
    
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #1E2A3A;
        border: 1px solid #334155;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
        color: #F1F5F9;
    }

</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

try:
    database.init_db()
except Exception as e:
    st.error(f"Gagal menginisialisasi database: {e}")
    st.error("Pastikan Anda telah menghapus file 'users.db' lama agar tabel baru bisa dibuat.")

# --- Variabel Sesi ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'login_step' not in st.session_state:
    st.session_state['login_step'] = 1
if 'login_username' not in st.session_state:
    st.session_state['login_username'] = ""
if 'login_password' not in st.session_state:
    st.session_state['login_password'] = ""
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
# --- AKHIR STATE BARU ---


# --- Bagian 1: Fungsi Tampilan Login & Logout (Diperbarui) ---

def login_form():
    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        st.title("AetherSecure", anchor=False)
        
        tab_login, tab_register = st.tabs(["🔒 Login", "✍️ Registrasi Pengguna Baru"])
        
        with tab_login:
            if st.session_state['login_step'] == 1:
                with st.form("login_form_credentials"):
                    st.markdown("##### Langkah 1: Masukkan Kredensial")
                    username = st.text_input("Username", placeholder="Masukkan username Anda")
                    password = st.text_input("Master Password", type="password", placeholder="Masukkan password Anda")
                    st.markdown("---") 
                    step1_button = st.form_submit_button("Lanjut ke Verifikasi Wajah 📸", use_container_width=True, type="primary")
                    if step1_button:
                        if not username or not password:
                            st.error("Username dan Password tidak boleh kosong.")
                        else:
                            st.session_state['login_username'] = username
                            st.session_state['login_password'] = password
                            st.session_state['login_step'] = 2
                            st.rerun()
            elif st.session_state['login_step'] == 2:
                st.markdown(f"##### Langkah 2: Verifikasi Wajah untuk **{st.session_state['login_username']}**")
                login_face_image = st.camera_input("Ambil foto untuk verifikasi login", key="login_cam")
                if login_face_image:
                    if st.button("Masuk 🔒", use_container_width=True, type="primary"):
                        with st.spinner("Memverifikasi kredensial dan wajah..."):
                            success, message = database.verify_user(st.session_state['login_username'], st.session_state['login_password'], login_face_image)
                        if success:
                            st.success(f"Login Berhasil! Selamat datang, {st.session_state['login_username']}.")
                            st.session_state['logged_in'] = True
                            st.session_state['username'] = st.session_state['login_username']
                            st.session_state['login_step'] = 1
                            st.session_state['login_username'] = ""
                            st.session_state['login_password'] = ""
                            st.session_state['page'] = "Crypto Tools" # Default page
                            st.rerun() 
                        else:
                            if "Wajah tidak cocok" in message or "Tidak ada wajah" in message:
                                st.error(f"Login Gagal: {message}. Silakan coba ambil foto lagi.")
                            else:
                                st.error(f"Login Gagal: {message}. Silakan kembali dan cek kredensial Anda.")
                                st.session_state['login_step'] = 1
                                st.session_state['login_username'] = ""
                                st.session_state['login_password'] = ""
                                st.rerun()
                if st.button("Kembali (Ganti Username/Password)", use_container_width=True):
                    st.session_state['login_step'] = 1
                    st.session_state['login_username'] = ""
                    st.session_state['login_password'] = ""
                    st.rerun()

        with tab_register:
            st.info("Username bersifat unik dan password akan di-hash. Wajah Anda akan disimpan sebagai data encoding.", icon="ℹ️")
            if st.session_state['register_step'] == 1:
                with st.form("register_form_credentials"):
                    st.markdown("##### Langkah 1: Buat Akun Baru")
                    new_username = st.text_input("Username Baru", placeholder="Pilih username unik")
                    new_password = st.text_input("Password Baru", type="password", placeholder="Minimal 8 karakter")
                    confirm_password = st.text_input("Konfirmasi Password", type="password", placeholder="Ulangi password")
                    st.markdown("---") 
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
                st.warning("Pastikan wajah Anda terlihat jelas di tengah dan hanya ada satu wajah di foto.", icon="⚠️")
                register_face_image = st.camera_input("Ambil foto untuk registrasi biometrik", key="reg_cam")
                if register_face_image:
                    if st.button("Daftar 👤", use_container_width=True, type="primary"):
                        with st.spinner("Memproses gambar wajah dan membuat akun..."):
                            success, message = database.add_user(st.session_state['reg_username'], st.session_state['reg_password'], register_face_image)
                        if success:
                            st.success(f"Pengguna '{st.session_state['reg_username']}' berhasil dibuat! Silakan login.", icon="✅")
                            st.session_state['register_step'] = 1
                            st.session_state['reg_username'] = ""
                            st.session_state['reg_password'] = ""
                        else:
                            if "Tidak ada wajah" in message:
                                st.error(f"Registrasi Gagal: {message}. Silakan coba ambil foto lagi.")
                            else:
                                st.error(f"Registrasi Gagal: {message}")
                                st.session_state['register_step'] = 1
                                st.session_state['reg_username'] = ""
                                st.session_state['reg_password'] = ""
                                st.rerun()
                if st.button("Kembali (Ganti Username/Password)", use_container_width=True, key="reg_back"):
                    st.session_state['register_step'] = 1
                    st.session_state['reg_username'] = ""
                    st.session_state['reg_password'] = ""
                    st.rerun()

def logout():
    st.session_state['logged_in'] = False
    st.session_state['username'] = None
    st.session_state['login_step'] = 1
    st.session_state['login_username'] = ""
    st.session_state['login_password'] = ""
    st.session_state['register_step'] = 1
    st.session_state['reg_username'] = ""
    st.session_state['reg_password'] = ""
    st.session_state['page'] = "Crypto Tools"
    st.session_state['selected_message_id'] = None
    st.success("Anda telah keluar dengan aman.")


# --- Bagian 2: Tampilan Konten Utama (DIROMBAK TOTAL) ---

def render_crypto_tools_page():
    """Menampilkan 3 tab enkripsi (Teks, Gambar, File)."""
    st.title("🛡️ AetherSecure Crypto Vault", anchor=False)
    
    tab_text, tab_image, tab_file = st.tabs([
        "💬 **Pesan Teks (Super Enkripsi)**", 
        "🖼️ **Gambar (Steganografi)**", 
        "🗄️ **Enkripsi File (AES)**"
    ])

    with tab_text:
        st.header("Super Enkripsi Teks")
        st.markdown("Menggabungkan **Caesar Cipher** (Klasik) dan **XOR Cipher** (Stream) untuk keamanan berlapis.")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Input 📝")
            mode = st.radio("Pilih Mode Teks", ["Enkripsi", "Dekripsi"], key="text_mode", horizontal=True)
            text_input = st.text_area("Teks Input", height=150, placeholder="Ketik atau tempel teks Anda di sini...")
            with st.expander("Pengaturan Kunci 🔑"):
                caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3)
                xor_key = st.text_input("XOR Key (Kunci 2)", type="password", placeholder="Masukkan kunci rahasia XOR")
        with col2:
            st.subheader("Output 💡")
            if st.button(f"Proses {mode} Teks ⚡", use_container_width=True, type="primary"):
                if text_input and xor_key:
                    with st.status(f"Melakukan {mode} teks...") as status:
                        try:
                            if mode == "Enkripsi":
                                status.update(label="Langkah 1: Enkripsi Caesar...", state="running")
                                status.update(label="Langkah 2: Enkripsi XOR & Base64...", state="running")
                                result = crypto.super_encrypt_text(text_input, caesar_shift, xor_key)
                                st.code(result, language=None)
                                st.info("Teks di atas adalah hasil enkripsi (Caesar -> XOR -> Base64).")
                                status.update(label="Enkripsi Teks Berhasil! ✅", state="complete")
                            else:
                                status.update(label="Langkah 1: Dekode Base64 & Dekripsi XOR...", state="running")
                                status.update(label="Langkah 2: Dekripsi Caesar...", state="running")
                                result = crypto.super_decrypt_text(text_input, caesar_shift, xor_key)
                                st.text_area("Hasil Dekripsi:", value=result, height=150, disabled=True)
                                status.update(label="Dekripsi Teks Berhasil! ✅", state="complete")
                        except Exception as e:
                            status.update(label=f"Error: {e} ❌", state="error")
                else:
                    st.warning("Mohon masukkan Teks dan Kunci XOR. ⚠️")

    with tab_image:
        st.header("StegoImage Sender")
        st.markdown("Menyembunyikan pesan teks rahasia di dalam gambar (Format PNG) menggunakan metode **Least Significant Bit (LSB)**.")
        st.divider()
        mode = st.radio("Pilih Mode Steganografi", ["Sisipkan Pesan 🔽", "Ekstrak Pesan 🔼"], key="image_mode", horizontal=True)
        if mode == "Sisipkan Pesan 🔽":
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Input 📝")
                image_file = st.file_uploader("Upload Gambar Penampung (Cover Image)", type=["png"])
                message_to_hide = st.text_area("Pesan Rahasia", height=150, placeholder="Pesan rahasia ini akan disisipkan ke gambar...")
            with col2:
                st.subheader("Output 💡")
                if st.button("Sisipkan Pesan ke Gambar 🖼️", use_container_width=True, type="primary"):
                    if image_file and message_to_hide:
                        with st.status("Menyisipkan pesan ke gambar...") as status:
                            try:
                                image_bytes = image_file.getvalue()
                                status.update(label="Memproses LSB...", state="running")
                                stego_image_bytes = crypto.stego_hide_message(image_bytes, message_to_hide)
                                st.image(stego_image_bytes, caption="Gambar Stego (Hasil)")
                                st.download_button(label="Download Gambar Stego (PNG) 💾", data=stego_image_bytes, file_name="stego_image.png", mime="image/png", use_container_width=True)
                                status.update(label="Pesan Berhasil Disisipkan! ✅", state="complete")
                            except Exception as e:
                                status.update(label=f"Error: {e} ❌", state="error")
                    else:
                        st.warning("Mohon upload gambar PNG dan isi pesan rahasia. ⚠️")
        else:
            st.subheader("Input 📝")
            stego_image_file = st.file_uploader("Upload Gambar Stego (PNG)", type=["png"])
            if st.button("Ekstrak Pesan dari Gambar 🔍", use_container_width=True, type="primary"):
                if stego_image_file:
                    with st.status("Mengekstrak pesan dari gambar...") as status:
                        try:
                            stego_bytes = stego_image_file.getvalue()
                            status.update(label="Membaca LSB...", state="running")
                            extracted_message = crypto.stego_extract_message(stego_bytes)
                            st.subheader("Output 💡")
                            st.text_area("Pesan Rahasia Ditemukan:", value=extracted_message, height=150, disabled=True)
                            status.update(label="Pesan Berhasil Diekstrak! ✅", state="complete")
                        except Exception as e:
                            status.update(label=f"Error: {e} ❌", state="error")
                else:
                    st.warning("Mohon upload gambar stego PNG. ⚠️")

    with tab_file:
        st.header("CryptoVault File Security")
        st.markdown("Mengamankan file (dokumen, database, dll.) menggunakan **AES-256-GCM** (Kriptografi Modern).")
        st.warning("Gunakan password yang kuat dan **JANGAN LUPAKAN** password tersebut. File tidak dapat dipulihkan tanpanya.", icon="⚠️")
        st.divider()
        mode = st.radio("Pilih Mode File", ["Enkripsi File 🔒", "Dekripsi File 🔓"], key="file_mode", horizontal=True)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Input 📝")
            file_to_process = st.file_uploader("Upload File", type=None, label_visibility="collapsed", help="Upload file yang ingin diproses")
            file_key = st.text_input("Password File", type="password", key="file_key", placeholder="Masukkan password untuk file ini")
        with col2:
            st.subheader("Output 💡")
            if st.button(f"Proses {mode} ⚡", use_container_width=True, type="primary"):
                if file_to_process and file_key:
                    with st.status(f"Melakukan {mode}...") as status:
                        try:
                            original_filename = file_to_process.name
                            file_bytes = file_to_process.getvalue()
                            status.update(label="Memproses file...", state="running")
                            if mode == "Enkripsi File 🔒":
                                encrypted_bytes = crypto.aes_encrypt_file(file_bytes, file_key)
                                new_filename = f"{original_filename}.enc"
                                st.download_button(label=f"Download File Terenkripsi ({new_filename}) 💾", data=encrypted_bytes, file_name=new_filename, mime="application/octet-stream", use_container_width=True)
                                status.update(label="File Berhasil Dienkripsi! ✅", state="complete")
                            else:
                                decrypted_bytes = crypto.aes_decrypt_file(file_bytes, file_key)
                                if original_filename.endswith(".enc"):
                                    new_filename = original_filename[:-4]
                                else:
                                    new_filename = f"decrypted_{original_filename}"
                                st.download_button(label=f"Download File Asli ({new_filename}) 💾", data=decrypted_bytes, file_name=new_filename, mime="application/octet-stream", use_container_width=True)
                                status.update(label="File Berhasil Didekripsi! ✅", state="complete")
                        except Exception as e:
                            status.update(label=f"DEKRIPSI GAGAL. Password salah atau file rusak. ❌", state="error")
                else:
                    st.warning("Mohon upload file dan masukkan password. ⚠️")

def render_messaging_page():
    """Menampilkan halaman baru untuk mengirim dan menerima pesan terenkripsi."""
    st.title("📨 Pesan Aman Terenkripsi", anchor=False)
    
    tab_inbox, tab_send = st.tabs(["📥 Kotak Masuk", "📬 Kirim Pesan Baru"])
    
    # --- 1. TAB KIRIM PESAN ---
    with tab_send:
        st.subheader("Kirim Pesan Terenkripsi Baru")
        
        all_users = database.get_all_usernames(exclude_user=st.session_state['username'])
        if not all_users:
            st.warning("Saat ini tidak ada pengguna lain untuk dikirimi pesan.", icon="👥")
            return

        recipient = st.selectbox("Pilih Penerima:", all_users)
        msg_type = st.radio("Pilih Tipe Pesan:", ["Teks Super Enkripsi", "Gambar Steganografi", "File AES"], horizontal=True, key="send_msg_type")
        
        data_to_send = None
        filename_to_send = None
        
        # Formulir akan muncul berdasarkan msg_type
        if msg_type == "Teks Super Enkripsi":
            text_input = st.text_area("Teks Plaintext:", placeholder="Ketik pesan rahasia Anda di sini...")
            st.markdown("Masukkan kunci untuk mengenkripsi pesan ini:")
            col1, col2 = st.columns(2)
            with col1:
                caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3, key="send_caesar")
            with col2:
                xor_key = st.text_input("XOR Key (Kunci 2)", type="password", placeholder="Kunci rahasia XOR", key="send_xor")
            
            if st.button("Kirim Pesan Teks 🚀", use_container_width=True, type="primary"):
                if text_input and xor_key and recipient:
                    encrypted_text = crypto.super_encrypt_text(text_input, caesar_shift, xor_key)
                    data_to_send = encrypted_text # Ini adalah string Base64
                    filename_to_send = "pesan_teks.txt"
                else:
                    st.warning("Mohon lengkapi semua field.")
                    
        elif msg_type == "Gambar Steganografi":
            image_file = st.file_uploader("Upload Gambar Penampung (Cover Image)", type=["png"], key="send_stego_img")
            message_to_hide = st.text_area("Pesan Rahasia untuk Disisipkan:", placeholder="Pesan ini akan disisipkan ke gambar...")
            
            if st.button("Kirim Pesan Gambar 🚀", use_container_width=True, type="primary"):
                if image_file and message_to_hide and recipient:
                    with st.spinner("Memproses gambar steganografi..."):
                        try:
                            image_bytes = image_file.getvalue()
                            stego_image_bytes = crypto.stego_hide_message(image_bytes, message_to_hide)
                            data_to_send = stego_image_bytes # Ini adalah bytes
                            filename_to_send = f"stego_{image_file.name}"
                        except Exception as e:
                            st.error(f"Error steganografi: {e}")
                else:
                    st.warning("Mohon lengkapi semua field.")
                            
        elif msg_type == "File AES":
            file_to_process = st.file_uploader("Upload File untuk Dienkripsi", type=None, key="send_aes_file")
            file_key = st.text_input("Password File AES", type="password", placeholder="Password untuk file ini", key="send_aes_key")

            if st.button("Kirim File AES 🚀", use_container_width=True, type="primary"):
                if file_to_process and file_key and recipient:
                    with st.spinner("Mengenkripsi file dengan AES..."):
                        try:
                            file_bytes = file_to_process.getvalue()
                            encrypted_bytes = crypto.aes_encrypt_file(file_bytes, file_key)
                            data_to_send = encrypted_bytes # Ini adalah bytes
                            filename_to_send = f"{file_to_process.name}.enc"
                        except Exception as e:
                            st.error(f"Error enkripsi file AES: {e}")
                else:
                    st.warning("Mohon lengkapi semua field.")

        # Logika Pengiriman Pesan Universal
        if data_to_send is not None:
            success, message = database.send_message(
                sender=st.session_state['username'],
                recipient=recipient,
                msg_type=msg_type,
                data=data_to_send,
                filename=filename_to_send
            )
            if success:
                st.success(f"Pesan terenkripsi berhasil dikirim ke **{recipient}**! ✅")
                st.info("PENTING: Beri tahu penerima kunci/password yang Anda gunakan melalui cara lain (misal: chat pribadi).", icon="🔑")
            else:
                st.error(message)

    # --- 2. TAB KOTAK MASUK ---
    with tab_inbox:
        st.subheader("Kotak Masuk Anda")
        
        # Tampilkan pesan yang dipilih (jika ada) DI BAGIAN ATAS
        if 'selected_message_id' in st.session_state and st.session_state['selected_message_id'] is not None:
            render_message_detail(st.session_state['selected_message_id'])

        st.divider()
        st.subheader("Daftar Pesan:")
        
        my_messages = database.get_messages_for_user(st.session_state['username'])
        
        if not my_messages:
            st.info("Anda belum memiliki pesan masuk.")
            return

        # Tampilkan daftar pesan dalam layout kartu yang rapi
        for msg in my_messages:
            msg_id = msg['id']
            sender = msg['sender_username']
            msg_type = msg['message_type']
            filename = msg['original_filename']
            timestamp = msg['timestamp']
            
            # Jangan tampilkan pesan yang sedang dibuka
            if msg_id == st.session_state.get('selected_message_id'):
                continue
            
            ts = datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d %b %Y, %H:%M')
            
            # Gunakan container border untuk setiap kartu pesan
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1.5])
                with col1:
                    st.markdown(f"**Dari:** `{sender}`")
                    st.caption(f"Diterima: {ts}")
                with col2:
                    st.markdown(f"**Tipe:**")
                    st.caption(f"{msg_type}")
                with col3:
                    st.button("Buka & Dekripsi 🔑", key=f"open_{msg_id}", use_container_width=True, on_click=lambda mid=msg_id: st.session_state.update(selected_message_id=mid))

def render_message_detail(message_id):
    """Menampilkan UI dekripsi untuk pesan yang dipilih di dalam container."""
    
    # Bungkus detail pesan dalam container (kartu)
    with st.container(border=True):
        st.subheader(f"Membuka Pesan #{message_id}")
        
        message = database.get_message_by_id(message_id)
        if not message:
            st.error("Pesan tidak ditemukan.")
            st.session_state['selected_message_id'] = None
            return

        sender, msg_type, encrypted_data_blob, filename = message
        
        st.info(f"Pesan ini dari **{sender}** | Tipe: **{msg_type}** | File: **{filename}**")
        st.markdown("Masukkan kunci yang sesuai (yang diberikan oleh pengirim) untuk mendekripsi pesan ini.")

        if msg_type == "Teks Super Enkripsi":
            col1, col2 = st.columns(2)
            with col1:
                caesar_shift = st.slider("Caesar Shift (Kunci 1)", 1, 25, 3, key="decrypt_caesar")
            with col2:
                xor_key = st.text_input("XOR Key (Kunci 2)", type="password", placeholder="Kunci rahasia XOR", key="decrypt_xor")
            
            if st.button("Dekripsi Teks ⚡", use_container_width=True, type="primary"):
                if xor_key:
                    try:
                        base64_ciphertext = encrypted_data_blob.decode('utf-8')
                        plaintext = crypto.super_decrypt_text(base64_ciphertext, caesar_shift, xor_key)
                        st.text_area("Hasil Dekripsi:", value=plaintext, height=150, disabled=True)
                    except Exception as e:
                        st.error(f"Gagal mendekripsi: {e}")
                else:
                    st.warning("Mohon masukkan Kunci XOR.")

        elif msg_type == "Gambar Steganografi":
            st.markdown("Klik tombol di bawah untuk men-download gambar. Anda harus membukanya di tab 'Gambar (Steganografi)' di halaman 'Crypto Tools' untuk mengekstrak pesannya.")
            st.download_button(
                label=f"Download Gambar Stego ({filename}) 💾",
                data=encrypted_data_blob,
                file_name=filename,
                mime="image/png",
                use_container_width=True
            )

        elif msg_type == "File AES":
            file_key = st.text_input("Password File AES", type="password", placeholder="Password untuk file ini", key="decrypt_aes_key")
            if st.button("Dekripsi File ⚡", use_container_width=True, type="primary"):
                if file_key:
                    try:
                        decrypted_bytes = crypto.aes_decrypt_file(encrypted_data_blob, file_key)
                        if filename.endswith(".enc"):
                            new_filename = filename[:-4]
                        else:
                            new_filename = f"decrypted_{filename}"
                            
                        st.download_button(
                            label=f"Download File Asli ({new_filename}) 💾",
                            data=decrypted_bytes,
                            file_name=new_filename,
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                        st.success("File berhasil didekripsi!")
                    except Exception as e:
                        st.error(f"DEKRIPSI GAGAL. Password salah atau file rusak. ❌")
                else:
                    st.warning("Mohon masukkan password file.")

        st.divider()
        if st.button("Tutup Pesan Ini 🔼", use_container_width=True):
            st.session_state['selected_message_id'] = None
            st.rerun()


def main_app_content():
    
    # --- NAVIGASI SIDEBAR (GAMBAR DIHAPUS) ---
    st.sidebar.title(f"Selamat Datang,\n{st.session_state['username']}!")
    
    st.session_state.page = st.sidebar.radio(
        "Menu Navigasi",
        ["🧰 Crypto Tools", "📨 Pesan Aman"],
        key="nav_radio"
    )
    
    st.sidebar.button("Logout 🚪", on_click=logout, use_container_width=True, type="primary")
    st.sidebar.divider()
    st.sidebar.header("Tentang Aplikasi")
    st.sidebar.info("AetherSecure adalah vault kriptografi berlapis untuk mengamankan data teks, gambar, dan file Anda.")

    if st.session_state.page == "🧰 Crypto Tools":
        render_crypto_tools_page()
    elif st.session_state.page == "📨 Pesan Aman":
        render_messaging_page()
    

# --- Bagian 3: Logika Utama (Menampilkan Login atau Konten Aplikasi) ---
if st.session_state['logged_in']:
    main_app_content()
else:
    login_form()

