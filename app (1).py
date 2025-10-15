import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# ==============================================================================
# KONFIGURASI APLIKASI STREAMLIT
# ==============================================================================

st.set_page_config(
    page_title="Gemini Chatbot Kuliner 🧑‍🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Gemini Chatbot Ahli Kuliner 🧑‍🍳")

# ==============================================================================
# PENGATURAN MODEL DAN API KEY DARI SIDEBAR
# ==============================================================================

# Definisikan model yang tersedia
AVAILABLE_MODELS = {
    'Gemini 1.5 Flash (Direkomendasikan)': 'gemini-1.5-flash',
    'Gemini 2.5 Flash Lite': 'gemini-2.5-flash-lite',
    'Gemini 1.0 Pro': 'gemini-1.0-pro'
}

with st.sidebar:
    st.header("Konfigurasi API ⚙️")

    # Input API Key
    st.caption("Masukkan Gemini API Key Anda. Tidak disimpan oleh aplikasi ini.")
    # Anda bisa menggunakan st.secrets['GEMINI_API_KEY'] jika di-deploy di Streamlit Community Cloud
    api_key_input = st.text_input(
        "API Key",
        type="password",
        placeholder="AIzaSy...",
        key="api_key_input"
    )

    # Pilihan Model
    model_display_name = st.selectbox(
        "Pilih Model Gemini",
        list(AVAILABLE_MODELS.keys())
    )
    MODEL_NAME = AVAILABLE_MODELS[model_display_name]

    st.divider()

    st.header("Sistem Prompt 💡")
    # Definisikan peran chatbot (diadaptasi dari INITIAL_CHATBOT_CONTEXT Anda)
    SYSTEM_INSTRUCTION = (
        "Kamu adalah ahli Kuliner. Berikan lokasi kuliner yang direkomendasikan. "
        "Jawaban harus singkat dan jelas. "
        "Tolak pertanyaan yang tidak berhubungan dengan lokasi kuliner."
    )
    st.text_area(
        "Instruksi Sistem (Peran Chatbot)",
        SYSTEM_INSTRUCTION,
        height=150,
        key="system_instruction_area"
    )

    st.divider()
    st.write("Dibuat dengan Gemini API dan Streamlit.")


# ==============================================================================
# INISIALISASI GEMINI DAN SESI STATE
# ==============================================================================

# Riwayat chat disimpan di session state agar tidak hilang saat UI refresh
if "messages" not in st.session_state:
    st.session_state.messages = []

# Objek chat disimpan di session state
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

def init_gemini(api_key, model_name, system_instruction):
    """Mengkonfigurasi Gemini dan menginisialisasi sesi chat."""
    if not api_key:
        st.error("Masukkan Gemini API Key di sidebar untuk memulai.")
        return False

    try:
        # Konfigurasi API
        genai.configure(api_key=api_key)

        # Inisialisasi Model
        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=500
            ),
            # Pengaturan keamanan agar lebih fleksibel (opsional)
            safety_settings=[
                genai.types.SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                )
            ]
        )

        # Inisialisasi sesi chat baru
        st.session_state.chat_session = model.start_chat(history=[])
        st.session_state.messages = [
             {"role": "model", "content": "Halo! Saya siap merekomendasikan tempat kuliner terbaik. Tanyakan saja lokasi yang Anda cari!"}
        ]

        st.success(f"Model **{model_name}** berhasil dikonfigurasi. Silakan mulai chat.")
        return True

    except Exception as e:
        st.error(f"Kesalahan saat menginisialisasi Gemini: {e}")
        st.error("Pastikan API Key Anda benar dan kuota tersedia.")
        return False

# Tombol untuk inisialisasi/reset chat
if st.sidebar.button("Mulai Chat / Reset Chat"):
    init_gemini(api_key_input, MODEL_NAME, SYSTEM_INSTRUCTION)


# ==============================================================================
# LOGIKA UTAMA CHATBOT (STREAMLIT UI)
# ==============================================================================

# Tampilkan riwayat chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Fungsi untuk mengirim pesan dan mendapatkan respons
def send_message(prompt):
    """Mengirim pesan ke model Gemini dan menambahkan ke riwayat."""
    if not st.session_state.chat_session:
        st.error("Chatbot belum diinisialisasi. Tekan 'Mulai Chat / Reset Chat' di sidebar.")
        return

    # Tambahkan pesan pengguna ke riwayat
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Tampilkan pesan pengguna
    with st.chat_message("user"):
        st.write(prompt)

    # Kirim pesan ke Gemini
    try:
        with st.chat_message("model"):
            with st.spinner("Gemini sedang berpikir..."):
                response = st.session_state.chat_session.send_message(
                    prompt, 
                    request_options={"timeout": 60}
                )
                
                # Tampilkan dan simpan respons
                model_response = response.text
                st.write(model_response)
                st.session_state.messages.append({"role": "model", "content": model_response})

    except Exception as e:
        error_message = f"Terjadi kesalahan: {e}. Coba lagi atau reset chat."
        with st.chat_message("model"):
            st.error(error_message)
        st.session_state.messages.append({"role": "model", "content": error_message})


# Input pengguna di bagian bawah
user_input = st.chat_input("Tanyakan lokasi kuliner yang Anda cari...")

if user_input:
    send_message(user_input)
