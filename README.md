# MetaSpin — Ray-Ban Meta Story Converter

Convert regular photos and videos into **Ray-Ban Meta Smart Glasses** format so that Instagram enables the interactive **Spin View (👓)** feature on Stories.

---

## ✨ Features

- **QuickTime Atom Restructuring**: Rewrites MP4/MOV container structure with authentic Ray-Ban Meta atoms (`ftyp`, `mvhd`, `tkhd`, `tapt`, `hdlr`, `keys`, `ilst`).
- **iOS & Hardware Decoder Safe**: Encodes with limited-range `yuv420p` BT.2020 HLG, avoiding crashes on iPhone A15+ Bionic chips.
- **Adjustable Story Duration**: Choose between `5s`, `10s` (ideal), or `15s` for story playback.
- **Dual Output**: Generates both interactive `.MOV` (Spin View) and `.JPG` with Ray-Ban hardware EXIF tags.
- **Mobile-First Utility Interface**: Clean dark UI optimized for Safari (iOS) and Chrome (Android).

---

## 🚀 Cara Penggunaan (Tutorial untuk Followers IG)

1. Buka web converter di browser HP kamu.
2. Pilih foto dari galeri HP.
3. Pilih durasi video (disarankan **10 Detik**).
4. Tekan **Mulai Konversi**.
5. Tekan **Download Spin View (.MOV)**.
6. **Khusus iPhone (Safari):**
   - Tap ikon **Share (kotak panah ke atas)** di Safari.
   - Pilih **"Save Video" (Simpan Video)** agar tersimpan ke aplikasi **Photos / Galeri**, bukan cuma di folder Downloads.
7. **Buka Instagram Story:**
   - Pilih video yang baru disimpan.
   - Tap **ikon kacamata 👓** di menu atas atau di thumbnail.
   - Aktifkan **"Spin View"** lalu posting!

---

## 🛠️ Menjalankan di Lokal (Self-Host)

### Prasyarat
- Python 3.10+
- `ffmpeg` terinstall di sistem

### Instalasi
```bash
git clone https://github.com/HeReffz/metaspin.git
cd metaspin
pip install -r requirements.txt
```

### Menjalankan Server Lokal
```bash
python app.py
```
Buka browser di `http://localhost:5000`.

### Menjalankan dengan Cloudflare Tunnel (Akses dari HP)
```bash
python run_with_tunnel.py
```
Script akan otomatis membuat tunnel HTTPS publik gratis dan menampilkan QR Code di terminal untuk di-scan lewat HP.

---

## ☁️ Deploy ke Cloud (Gratis)

Project ini sudah dilengkapi dengan `Dockerfile`, siap di-deploy ke platform yang mendukung Docker:

- **Render.com**: Buat *New Web Service* -> Connect repo GitHub -> Pilih Environment *Docker* -> Deploy.
- **Railway.app**: New Project -> Deploy from GitHub repo.
- **Hugging Face Spaces**: Create new Space -> SDK: *Docker* -> Push repo.

---

## 📜 Lisensi
MIT License.
