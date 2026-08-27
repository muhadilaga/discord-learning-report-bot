import os
from urllib.parse import parse_qs, urlparse

from google_auth_oauthlib.flow import InstalledAppFlow

GOOGLE_OAUTH_CLIENT_SECRET_FILE = os.getenv(
    "GOOGLE_OAUTH_CLIENT_SECRET_FILE",
    "/root/discord-learning-report-bot/google-client-secret.json",
)
GOOGLE_OAUTH_TOKEN_FILE = os.getenv(
    "GOOGLE_OAUTH_TOKEN_FILE",
    "/root/discord-learning-report-bot/google-token.json",
)
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


if not os.path.exists(GOOGLE_OAUTH_CLIENT_SECRET_FILE):
    raise RuntimeError(
        "File OAuth client secret Google tidak ditemukan di: "
        f"{GOOGLE_OAUTH_CLIENT_SECRET_FILE}"
    )

flow = InstalledAppFlow.from_client_secrets_file(
    GOOGLE_OAUTH_CLIENT_SECRET_FILE,
    GOOGLE_SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob",
)
auth_url, _ = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes="true",
)

print("Buka URL ini di browser HP Anda, login, lalu izinkan akses:")
print(auth_url)
print()
user_input = input(
    "Paste verification code ATAU URL redirect lengkap di sini, lalu Enter: "
).strip()

if user_input.startswith("http://") or user_input.startswith("https://"):
    parsed = urlparse(user_input)
    code = parse_qs(parsed.query).get("code", [""])[0]
    if not code:
        raise RuntimeError("Parameter code tidak ditemukan pada URL yang Anda paste.")
else:
    code = user_input

flow.fetch_token(code=code)
creds = flow.credentials

with open(GOOGLE_OAUTH_TOKEN_FILE, "w", encoding="utf-8") as token:
    token.write(creds.to_json())

print(f"Token Google berhasil disimpan di: {GOOGLE_OAUTH_TOKEN_FILE}")

if creds.refresh_token:
    print("Refresh token tersedia: YA")
else:
    print("Refresh token tersedia: TIDAK")

print("Otorisasi Google Sheets selesai.")

if False:
    pass

if __name__ == "__main__":
    pass

# script body sengaja tetap top-level agar sederhana untuk penggunaan HP
# dan mudah dijalankan langsung via python3 authorize_google.py
# tanpa perlu argumen tambahan.

# Keep a harmless final line so file ends cleanly.
print("Siap menerima input otorisasi.") if False else None
