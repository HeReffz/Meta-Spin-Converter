import os
import re
import subprocess
import sys
import threading
import time
import qrcode

# Set UTF-8 encoding for terminal output (QR code support on Windows)
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import app


def run_flask():
    # Run Flask in background thread
    import logging
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


def main():
    print("=" * 60)
    print("🚀 MEMULAI RAY-BAN META SPIN VIEW CONVERTER WEB")
    print("=" * 60)
    print("Menjalankan server backend lokal...")

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(1.5)

    print("Membuka jalur tunnel Cloudflare (trycloudflare)...")
    cloudflared_cmd = ["cloudflared", "tunnel", "--url", "http://127.0.0.1:5000"]
    
    proc = subprocess.Popen(
        cloudflared_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    tunnel_url = None
    pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")

    # Read stderr of cloudflared to find tunnel URL
    for line in iter(proc.stderr.readline, ""):
        match = pattern.search(line)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        print("❌ Gagal mendapatkan URL Cloudflare Tunnel.")
        return

    print("\n" + "✨" * 30)
    print(f"🎉 WEB SIAP DIAKSES DARI HP KAMU!")
    print(f"👉 Link Publik: {tunnel_url}")
    print("✨" * 30 + "\n")

    print("📱 Scan QR Code di bawah pakai Kamera HP untuk langsung buka:")
    try:
        qr = qrcode.QRCode(border=2)
        qr.add_data(tunnel_url)
        qr.print_ascii(invert=True)
    except Exception as e:
        print(f"(QR code tidak dapat ditampilkan: {e})")

    print("\n💡 Panduan Penggunaan:")
    print("1. Buka link di atas pada browser HP (Safari / Chrome).")
    print("2. Pilih foto yang ingin di-convert.")
    print("3. Tekan 'Convert ke Ray-Ban Meta'.")
    print("4. Download hasilnya & simpan ke Galeri / Camera Roll (bukan di Files).")
    print("5. Buka Instagram Story -> pilih filenya -> tap ikon kacamata 👓 -> aktifkan Spin View!")
    print("\nTekan Ctrl + C di terminal ini jika ingin mematikan web server.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nMematikan server dan tunnel...")
        proc.terminate()
        print("Selesai!")


if __name__ == "__main__":
    main()
