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

# Custom CSS matching Gambar 1
st.markdown("""
<style>
    /* Hide Streamlit default branding */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    footer {
        display: none !important;
    }
    #MainMenu {
        display: none !important;
    }
    .stDeployButton {
        display: none !important;
    }

    /* Base Layout */
    .stApp {
        background-color: #0c0d0f !important;
        color: #f0f2f5 !important;
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }
    .main .block-container {
        max-width: 430px !important;
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: 0 auto !important;
    }

    /* Top Nav */
    .top-nav {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 14px;
    }
    .brand {
        display: flex;
        align-items: center;
        gap: 8px;
        font-weight: 600;
        font-size: 13.5px;
        color: #f0f2f5;
    }
    .brand-icon {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: #141619;
        border: 1px solid #22262c;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #f0f2f5;
    }
    .nav-guide-btn {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 500;
        color: #8c95a3;
        background: #141619;
        border: 1px solid #22262c;
        padding: 5px 11px;
        border-radius: 999px;
        text-decoration: none;
        transition: all 0.15s ease;
    }
    .nav-guide-btn:hover {
        color: #f0f2f5;
        border-color: #2c323a;
        background: #1a1d21;
    }

    /* Hero */
    .app-title {
        font-size: 20px;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #f0f2f5;
        margin-bottom: 6px;
    }
    .app-subtitle {
        font-size: 13px;
        color: #8c95a3;
        line-height: 1.45;
        margin-bottom: 18px;
    }

    /* Main Card Container */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #141619 !important;
        border: 1px solid #22262c !important;
        border-radius: 16px !important;
        padding: 18px !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3) !important;
        margin-bottom: 18px !important;
    }

    /* File Uploader styling */
    div[data-testid="stFileUploader"] {
        background: rgba(255, 255, 255, 0.01) !important;
        border: 1.5px dashed #2c323a !important;
        border-radius: 12px !important;
        padding: 14px !important;
        margin-bottom: 12px !important;
        transition: border-color 0.15s ease !important;
    }
    div[data-testid="stFileUploader"]:hover {
        border-color: #8c95a3 !important;
    }
    div[data-testid="stFileUploader"] section {
        padding: 0 !important;
    }
    div[data-testid="stFileUploader"] label p {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #8c95a3 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.02em !important;
    }

    /* Segmented Control / Duration Pills */
    div[data-testid="stSegmentedControl"] {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 6px !important;
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin-bottom: 14px !important;
    }
    div[data-testid="stSegmentedControl"] button {
        background: #0c0d0f !important;
        border: 1px solid #22262c !important;
        color: #8c95a3 !important;
        font-weight: 600 !important;
        font-size: 12.5px !important;
        border-radius: 8px !important;
        padding: 9px 0 !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stSegmentedControl"] button:hover {
        color: #f0f2f5 !important;
        border-color: #2c323a !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-checked="true"] {
        background: #1a1d21 !important;
        color: #f0f2f5 !important;
        border-color: #3b82f6 !important;
    }

    /* Fallback Radio Pills if segmented_control is rendered as radio */
    div[data-testid="stRadio"] div[role="radiogroup"] {
        display: grid !important;
        grid-template-columns: repeat(3, 1fr) !important;
        gap: 6px !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] label {
        background: #0c0d0f !important;
        border: 1px solid #22262c !important;
        border-radius: 8px !important;
        padding: 9px 4px !important;
        text-align: center !important;
        justify-content: center !important;
    }
    div[data-testid="stRadio"] label p {
        font-size: 12px !important;
        font-weight: 600 !important;
        color: #8c95a3 !important;
    }

    /* Action Button (Blue) */
    button[kind="primary"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 10px !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        padding: 13px !important;
        box-shadow: none !important;
        transition: background-color 0.15s ease !important;
        margin-top: 4px !important;
    }
    button[kind="primary"]:hover {
        background-color: #1d4ed8 !important;
    }

    /* Download Buttons */
    div[data-testid="stDownloadButton"]:first-of-type button {
        background-color: #10b981 !important;
        color: #042f2e !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 13.5px !important;
        padding: 12px !important;
    }
    div[data-testid="stDownloadButton"]:first-of-type button:hover {
        background-color: #059669 !important;
    }
    div[data-testid="stDownloadButton"]:last-of-type:not(:first-of-type) button {
        background-color: transparent !important;
        color: #8c95a3 !important;
        border: 1px solid #22262c !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 12px !important;
        padding: 10px !important;
    }
    div[data-testid="stDownloadButton"]:last-of-type:not(:first-of-type) button:hover {
        color: #f0f2f5 !important;
        border-color: #2c323a !important;
    }

    /* Video player styling */
    video {
        border-radius: 8px !important;
        border: 1px solid #22262c !important;
        background: #000 !important;
        margin: 10px 0 !important;
    }

    /* Guide Box */
    .guide-box {
        border: 1px solid #22262c;
        border-radius: 16px;
        background: #141619;
        padding: 14px 16px;
        margin-top: 12px;
    }
    .guide-title {
        font-size: 12.5px;
        font-weight: 600;
        color: #f0f2f5;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
    }
    .guide-steps {
        list-style: none;
        padding: 0;
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 6px;
    }
    .guide-steps li {
        font-size: 12px;
        color: #8c95a3;
        line-height: 1.45;
        display: flex;
        gap: 8px;
    }
    .guide-steps span {
        color: #586170;
        font-family: monospace;
        font-size: 11px;
    }
    .guide-steps strong {
        color: #f0f2f5;
    }
</style>
""", unsafe_allow_html=True)

# Top Bar with MetaSpin Branding & Cara Pakai Button
st.markdown("""
<nav class="top-nav">
    <div class="brand">
        <div class="brand-icon">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="6" cy="12" r="4"></circle>
                <circle cx="18" cy="12" r="4"></circle>
                <line x1="10" y1="12" x2="14" y2="12"></line>
            </svg>
        </div>
        <span>MetaSpin</span>
    </div>
    <a href="#panduan" class="nav-guide-btn">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
        </svg>
        <span>Cara Pakai</span>
    </a>
</nav>

<h1 class="app-title">Ray-Ban Meta Converter</h1>
<p class="app-subtitle">Ubah foto atau video biasa ke format metadata kacamata Ray-Ban Meta agar fitur Spin View aktif di Instagram Story.</p>
""", unsafe_allow_html=True)

# Main Card Container (Just like Gambar 1)
with st.container(border=True):
    # File Uploader
    uploaded_file = st.file_uploader(
        "PILIH FOTO ATAU VIDEO",
        type=["jpg", "jpeg", "png", "webp", "mov", "mp4"],
        label_visibility="visible",
        help="Format JPG, PNG, atau MOV"
    )

    # Duration Segmented Control (Pills with text)
    if hasattr(st, "segmented_control"):
        duration_label = st.segmented_control(
            "DURASI VIDEO STORY",
            options=["5 Detik", "10 Detik", "15 Detik"],
            default="10 Detik",
            label_visibility="visible"
        )
    elif hasattr(st, "pills"):
        duration_label = st.pills(
            "DURASI VIDEO STORY",
            options=["5 Detik", "10 Detik", "15 Detik"],
            default="10 Detik",
            label_visibility="visible"
        )
    else:
        duration_label = st.radio(
            "DURASI VIDEO STORY",
            options=["5 Detik", "10 Detik", "15 Detik"],
            index=1,
            horizontal=True
        )

    duration_map = {"5 Detik": 5, "10 Detik": 10, "15 Detik": 15}
    duration = duration_map.get(duration_label, 10)

    # Action Button
    convert_clicked = st.button(
        "Mulai Konversi",
        type="primary",
        use_container_width=True,
        disabled=(uploaded_file is None)
    )

    if convert_clicked and uploaded_file is not None:
        file_ext = os.path.splitext(uploaded_file.name)[1].lower()
        is_video = file_ext in [".mov", ".mp4", ".m4v"]

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

                    st.markdown("""
                    <div style="font-size: 12px; font-weight: 600; color: #10b981; margin-top: 14px; margin-bottom: 6px;">
                        ✓ Selesai Dikonversi
                    </div>
                    """, unsafe_allow_html=True)

                    # Video preview
                    st.video(mov_data)

                    # Download Buttons
                    st.download_button(
                        label="Download Spin View (.MOV)",
                        data=mov_data,
                        file_name=mov_filename,
                        mime="video/quicktime",
                        use_container_width=True
                    )

                    if jpg_data:
                        st.download_button(
                            label="Download Foto EXIF (.JPG)",
                            data=jpg_data,
                            file_name=jpg_filename,
                            mime="image/jpeg",
                            use_container_width=True
                        )

                except Exception as e:
                    st.error(f"Gagal mengonversi: {e}")

# Practical Guide Box (Just like Gambar 1)
st.markdown("""
<aside class="guide-box" id="panduan">
    <div class="guide-title">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
        </svg>
        <span>Cara Simpan di iPhone (Safari)</span>
    </div>
    <ul class="guide-steps">
        <li><span>01.</span> Tekan tombol <strong>Download Spin View (.MOV)</strong> di atas.</li>
        <li><span>02.</span> Tekan ikon <strong>Share</strong> di Safari, lalu pilih <strong>Save Video</strong> agar masuk ke aplikasi Photos/Galeri.</li>
        <li><span>03.</span> Buka <strong>Instagram Story</strong>, pilih videonya, lalu aktifkan ikon kacamata (Spin View).</li>
    </ul>
</aside>
""", unsafe_allow_html=True)
