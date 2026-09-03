import os
import time
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from converter import process_to_spin_mov, process_image_to_meta_jpg

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv"}


def cleanup_old_files():
    now = time.time()
    for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER]:
        for fname in os.listdir(folder):
            fpath = os.path.join(folder, fname)
            if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > 3600:
                try:
                    os.remove(fpath)
                except Exception:
                    pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert_file():
    cleanup_old_files()

    if "file" not in request.files:
        return jsonify({"success": False, "error": "Tidak ada file yang diunggah"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "Nama file kosong"}), 400

    filename = secure_filename(file.filename)
    if not filename:
        filename = f"upload_{int(time.time())}.jpg"

    ext = os.path.splitext(filename)[1].lower()
    is_img = ext in IMAGE_EXTENSIONS
    is_vid = ext in VIDEO_EXTENSIONS

    if not is_img and not is_vid:
        return jsonify({"success": False, "error": f"Format {ext} tidak didukung. Harap upload foto atau video."}), 400

    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    duration = request.form.get("duration", 10)
    try:
        duration = int(duration)
    except Exception:
        duration = 10

    try:
        mov_path = process_to_spin_mov(input_path, OUTPUT_FOLDER, is_video=is_vid, duration=duration)
        mov_filename = os.path.basename(mov_path)

        jpg_filename = None
        if is_img:
            base_name = os.path.splitext(filename)[0]
            jpg_name = f"{base_name}_META.JPG"
            jpg_path = os.path.join(OUTPUT_FOLDER, jpg_name)
            process_image_to_meta_jpg(input_path, jpg_path)
            jpg_filename = jpg_name

        return jsonify({
            "success": True,
            "mov_url": f"/download/{mov_filename}",
            "mov_filename": mov_filename,
            "jpg_url": f"/download/{jpg_filename}" if jpg_filename else None,
            "jpg_filename": jpg_filename
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/download/<path:filename>")
def download_file(filename):
    return send_from_directory(OUTPUT_FOLDER, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
