# Discord Bot Laporan Pembelajaran

Bot Discord ini membantu membuat **laporan kegiatan pembelajaran dengan format tetap** tanpa harus mengetik laporan panjang secara manual di channel Discord.

## Fitur utama
- Slash command `/lapor`
- Modal/form untuk isi laporan
- Laporan otomatis dikirim ke channel `#daily-standup`
- Laporan otomatis disimpan ke Google Sheets
- Validasi tanggal format `dd-mm-yyyy`
- Autocomplete/saran kelas berdasarkan data yang sudah pernah masuk ke Google Sheets
- Ringkasan formal otomatis pada setiap laporan
- Command rekap mingguan
- Command rekap bulanan
- Export PDF dari data laporan pada rentang tanggal tertentu
- **Tanpa batasan role**, sehingga semua anggota server bisa memakai bot ini

## Daftar command
### 1. `/lapor`
Digunakan untuk membuat laporan pembelajaran baru.

Parameter awal:
- `tanggal`
- `kelas`
- `materi`
- `durasi`
- `jumlah_hadir`

Setelah itu akan muncul modal untuk mengisi:
- Aktivitas Utama
- Hasil/Capaian
- Kendala
- Tindak Lanjut

### 2. `/rekap_mingguan`
Untuk melihat rekap laporan pada rentang tanggal tertentu.

Parameter:
- `mulai` → format `dd-mm-yyyy`
- `akhir` → format `dd-mm-yyyy`

### 3. `/rekap_bulanan`
Untuk melihat rekap laporan 1 bulan.

Parameter:
- `bulan` → angka 1 sampai 12
- `tahun` → contoh `2026`

### 4. `/export_pdf`
Untuk mengekspor laporan pada periode tertentu ke file PDF.

Parameter:
- `mulai` → format `dd-mm-yyyy`
- `akhir` → format `dd-mm-yyyy`
- `judul` → opsional

## Format laporan di Discord
Bot akan mengirim format seperti ini:

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
...

Hasil/Capaian:
...

Kendala:
...

Tindak Lanjut:
...
```

## Kolom Google Sheets
Setiap laporan disimpan ke kolom berikut:
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

## Struktur file
- `bot.py` → kode utama bot
- `authorize_google.py` → otorisasi Google OAuth
- `requirements.txt` → dependency Python
- `.env` → environment variable runtime
- `.env.example` → contoh environment variable

## Runtime service
Bot dijalankan sebagai systemd service:
- service name: `discord-learning-report-bot.service`

Command penting:
```bash
systemctl status discord-learning-report-bot.service
systemctl restart discord-learning-report-bot.service
journalctl -u discord-learning-report-bot.service -n 50 --no-pager
journalctl -u discord-learning-report-bot.service -f
```

## Catatan
- Bot ini sengaja **tanpa pembatasan role** agar semua anggota bisa mengirim laporan tanpa chat manual ke channel.
- Jika Google Sheets gagal, laporan Discord tetap dikirim.
- Data autocomplete kelas berasal dari data historis di Google Sheets.
- Export PDF mengambil data dari Google Sheets, bukan dari chat Discord langsung.
