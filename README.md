# Discord Learning Report Bot

Bot Discord berbasis Python untuk **otomatisasi laporan kegiatan pembelajaran** dengan format tetap, penyimpanan ke **Google Sheets**, rekap data, dan **export PDF**.

Project ini cocok untuk komunitas belajar, mentor, kelas informal, kelompok bootcamp, atau tim edukasi yang ingin menghindari chat laporan manual di channel Discord.

## Highlights
- Slash command Discord yang mudah dipakai
- Modal/form untuk input laporan naratif
- Otomatis kirim laporan ke channel `#daily-standup`
- Otomatis simpan laporan ke Google Sheets
- Validasi tanggal `dd-mm-yyyy`
- Autocomplete kelas/kelompok dari riwayat data Sheets
- Ringkasan formal otomatis pada setiap laporan
- Rekap mingguan dan bulanan
- Export laporan ke file PDF
- Tanpa pembatasan role: semua anggota server dapat memakai bot

## Features

### 1. Create learning reports
Command `/lapor` membuka alur input dua tahap:
- parameter singkat untuk data utama laporan
- modal untuk deskripsi aktivitas dan hasil pembelajaran

Field yang digunakan:
- tanggal
- kelas/kelompok
- materi
- durasi
- jumlah_hadir
- aktivitas utama
- hasil/capaian
- kendala
- tindak lanjut

### 2. Store reports in Google Sheets
Setiap laporan yang berhasil dikirim ke Discord juga akan ditambahkan ke Google Sheets pada worksheet yang ditentukan.

Kolom yang disimpan:
1. Tanggal
2. Kelas/Kelompok
3. Materi
4. Durasi
5. Jumlah Hadir
6. Aktivitas Utama
7. Hasil/Capaian
8. Kendala
9. Tindak Lanjut
10. Dikirim oleh
11. Server Discord

### 3. Weekly and monthly recap
Bot menyediakan command rekap untuk membantu melihat histori laporan:
- `/rekap_mingguan`
- `/rekap_bulanan`

### 4. PDF export
Command `/export_pdf` membuat file PDF berdasarkan data laporan pada rentang tanggal tertentu.

## Available Commands

### `/lapor`
Membuat laporan pembelajaran baru.

Parameter:
- `tanggal` — format `dd-mm-yyyy`
- `kelas`
- `materi`
- `durasi`
- `jumlah_hadir`

Setelah parameter awal diisi, bot akan membuka modal dengan field:
- Aktivitas Utama
- Hasil/Capaian
- Kendala
- Tindak Lanjut

### `/rekap_mingguan`
Melihat rekap laporan pada rentang tanggal tertentu.

Parameter:
- `mulai` — format `dd-mm-yyyy`
- `akhir` — format `dd-mm-yyyy`

### `/rekap_bulanan`
Melihat rekap laporan pada bulan tertentu.

Parameter:
- `bulan` — angka 1 sampai 12
- `tahun` — contoh `2026`

### `/export_pdf`
Mengekspor laporan ke PDF berdasarkan rentang tanggal.

Parameter:
- `mulai` — format `dd-mm-yyyy`
- `akhir` — format `dd-mm-yyyy`
- `judul` — opsional

## Example Report Output

```text
LAPORAN KEGIATAN PEMBELAJARAN

Tanggal: 26-08-2026
Kelas/Kelompok: XI RPL
Materi: Dasar HTML
Durasi: 90 menit
Jumlah Peserta Hadir: 28 siswa

Ringkasan Formal:
Pada tanggal 26-08-2026, kegiatan pembelajaran untuk kelas/kelompok XI RPL dilaksanakan dengan materi Dasar HTML selama 90 menit dengan jumlah peserta hadir 28 siswa.

Aktivitas Utama:
Penyampaian materi HTML dasar, diskusi, dan praktik membuat struktur halaman.

Hasil/Capaian:
Peserta mulai memahami struktur dasar HTML dan mampu membuat file HTML sederhana.

Kendala:
Sebagian peserta masih perlu pendampingan pada penggunaan tag dasar.

Tindak Lanjut:
Pertemuan berikutnya difokuskan pada latihan lanjutan dan pengenalan CSS dasar.
```

## Project Structure

```text
.
├── authorize_google.py
├── bot.py
├── LICENSE
├── README.md
├── requirements.txt
└── .env.example
```

## Requirements
- Python 3.10+
- Discord Bot Token
- Discord server dengan channel tujuan laporan
- Google OAuth client untuk akses Google Sheets
- Google Sheet yang dapat diedit oleh akun OAuth

## Installation

### 1. Clone repository
```bash
git clone https://github.com/muhadilaga/discord-learning-report-bot.git
cd discord-learning-report-bot
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Prepare environment file
Copy `.env.example` menjadi `.env`, lalu isi nilai yang dibutuhkan.

Contoh environment variable penting:
```env
DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
DISCORD_GUILD_ID=YOUR_GUILD_ID
REPORT_CHANNEL_NAME=daily-standup
GOOGLE_SHEETS_SPREADSHEET_ID=YOUR_SPREADSHEET_ID
GOOGLE_SHEETS_WORKSHEET_NAME=Laporan
GOOGLE_OAUTH_CLIENT_SECRET_FILE=/absolute/path/to/google-client-secret.json
GOOGLE_OAUTH_TOKEN_FILE=/absolute/path/to/google-token.json
```

## Google OAuth Setup
Project ini menggunakan OAuth akun Google biasa untuk akses Google Sheets.

### Step 1 — Download OAuth client JSON
Buat OAuth client tipe **Desktop App** di Google Cloud Console, lalu simpan file JSON di server.

### Step 2 — Authorize Google access
Jalankan:
```bash
python3 authorize_google.py
```

Ikuti URL login yang diberikan, lalu masukkan verification code ke terminal.

### Step 3 — Confirm spreadsheet access
Pastikan akun Google yang dipakai saat OAuth memiliki akses **Editor** ke spreadsheet target.

## Running the Bot

### Manual run
```bash
python3 bot.py
```

### Run as systemd service
Project ini cocok dijalankan sebagai service agar bot tetap aktif.

Command yang berguna:
```bash
systemctl status discord-learning-report-bot.service
systemctl restart discord-learning-report-bot.service
journalctl -u discord-learning-report-bot.service -n 50 --no-pager
journalctl -u discord-learning-report-bot.service -f
```

## GitHub Actions
Repository ini menyertakan workflow CI sederhana untuk:
- install dependency
- compile-check file Python
- memastikan import utama bot dapat dimuat

Workflow berada di:
```text
.github/workflows/ci.yml
```

## Security Notes
- Jangan commit file `.env`
- Jangan commit `google-token.json`
- Jangan commit `google-client-secret.json`
- Jangan commit virtual environment `.venv`
- Jika token GitHub atau Discord pernah terlanjur terbuka, segera rotate/revoke token tersebut

## Development Notes
- Data autocomplete kelas diambil dari histori Google Sheets
- Rekap dan export PDF membaca data dari Google Sheets, bukan dari message history Discord
- Jika pengiriman ke Google Sheets gagal, laporan Discord tetap akan dikirim lebih dulu

## License
Project ini menggunakan [MIT License](LICENSE).
