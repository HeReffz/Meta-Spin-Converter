import os
import tempfile
import streamlit as st
from converter import process_to_spin_mov, process_image_to_meta_jpg

st.set_page_config(
    page_title="Ray-Ban Meta Converter",
    page_icon="🕶️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom Styling for clean modern dark appearance
st.markdown("""
<style>
    /* Dark theme clean styling */
    .stApp {
        background-color: #0c0d0f;
        color: #f0f2f5;
    }
    .main .block-container {
        max-width: 460px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    h1 {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.02em;
        margin-bottom: 0.2rem !important;
    }
    .stCaption {
        font-size: 0.85rem !important;
        color: #8c95a3 !important;
        margin-bottom: 1.2rem !important;
    }
    div[data-testid="stFileUploader"] {
        background: #141619;
        border: 1px solid #22262c;
        border-radius: 12px;
        padding: 12px;
    }
    button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1rem !important;
    }
    button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }
    div[data-testid="stExpander"] {
        background: #141619;
        border: 1px solid #22262c !important;
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("Ray-Ban Meta Converter")
st.caption("Ubah foto atau video biasa ke format metadata kacamata Ray-Ban Meta agar fitur Spin View aktif di Instagram Story.")

uploaded_file = st.file_uploader(
    "Pilih Foto atau Video",
    type=["jpg", "jpeg", "png", "webp", "mov", "mp4"],
    help="Pilih foto atau video dari galeri HP kamu"
)

duration = st.select_slider(
    "Durasi Video Story (Detik)",
    options=[5, 10, 15],
    value=10,
    help="10 detik paling ideal untuk interaksi Spin View di Story"
)

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    is_video = file_ext in [".mov", ".mp4", ".m4v"]

    if st.button("Mulai Konversi", type="primary", use_container_width=True):
        with st.spinner("Sedang memproses dan menyusun metadata Meta..."):
            with tempfile.TemporaryDirectory() as tmp_dir:
                input_path = os.path.join(tmp_dir, uploaded_file.name)
                with open(input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                output_dir = os.path.join(tmp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)

                try:
                    mov_path = process_to_spin_mov(input_path, output_dir, is_video=is_video, duration=duration)
                    base_name = os.path.splitext(uploaded_file.name)[0]
                    mov_filename = f"{base_name}_SPIN.MOV"

                    jpg_data = None
                    jpg_filename = None
                    if not is_video:
                        jpg_filename = f"{base_name}_META.JPG"
                        jpg_path = os.path.join(output_dir, jpg_filename)
                        process_image_to_meta_jpg(input_path, jpg_path)
                        with open(jpg_path, "rb") as jf:
                            jpg_data = jf.read()

                    with open(mov_path, "rb") as mf:
                        mov_data = mf.read()

                    st.success("✓ Selesai Dikonversi!")

                    # Video preview
                    st.video(mov_data)

                    # Download Buttons
                    st.download_button(
                        label="📥 Download Spin View (.MOV)",
                        data=mov_data,
                        file_name=mov_filename,
                        mime="video/quicktime",
                        use_container_width=True
                    )

                    if jpg_data:
                        st.download_button(
                            label="🖼️ Download Foto EXIF (.JPG)",
                            data=jpg_data,
                            file_name=jpg_filename,
                            mime="image/jpeg",
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"Gagal mengonversi: {e}")

st.markdown("---")
with st.expander("📖 Panduan Simpan di iPhone (Safari)"):
    st.markdown("""
    1. Tekan tombol **Download Spin View (.MOV)** di atas.
    2. Tekan ikon **Share (kotak panah ke atas)** di Safari.
    3. Pilih **"Save Video" (Simpan Video)** agar masuk ke aplikasi **Photos / Galeri**, bukan cuma di folder Downloads.
    4. Buka **Instagram Story**, pilih videonya, lalu aktifkan **ikon kacamata 👓 (Spin View)**!
    """)
