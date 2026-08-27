# Contributing Guide

Terima kasih sudah tertarik berkontribusi pada project ini.

## Cara berkontribusi
- Fork repository ini
- Buat branch baru untuk perubahan Anda
- Lakukan perubahan kecil dan terfokus
- Pastikan code tetap rapi dan mudah dibaca
- Jalankan pengecekan dasar sebelum membuat pull request

## Langkah development
```bash
git clone https://github.com/muhadilaga/discord-learning-report-bot.git
cd discord-learning-report-bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m py_compile bot.py authorize_google.py
```

## Pull request checklist
- [ ] Perubahan relevan dan fokus
- [ ] Tidak memasukkan secret atau token
- [ ] README diperbarui jika perlu
- [ ] Sintaks Python lolos
- [ ] Sudah menjelaskan tujuan perubahan

## Pelaporan bug
Saat membuat bug report, mohon sertakan:
- langkah reproduksi
- perilaku yang diharapkan
- perilaku yang terjadi
- log error jika ada
- screenshot jika relevan

## Saran fitur
Silakan buat issue dengan penjelasan:
- masalah yang ingin diselesaikan
- solusi yang diusulkan
- dampak untuk user
