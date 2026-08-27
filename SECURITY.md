# Security Policy

## Supported Version
Versi aktif pada branch `main` dianggap sebagai versi yang didukung.

## Reporting a Vulnerability
Jika Anda menemukan celah keamanan:
- jangan publikasikan token, secret, atau exploit detail di issue publik
- hubungi maintainer secara privat jika memungkinkan
- jelaskan dampak, langkah reproduksi, dan saran perbaikan

## Sensitive Data Reminder
Project ini berinteraksi dengan:
- Discord bot token
- Google OAuth token
- Google client secret

Pastikan file berikut tidak pernah di-commit:
- `.env`
- `google-token.json`
- `google-client-secret.json`
