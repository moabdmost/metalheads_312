import os

# ── SMTP ──────────────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "noreplyDCQC@gmail.com"
SMTP_PASSWORD = "adct ymgm qikk kgsr"   # Gmail App Password

# ── Data file paths ───────────────────────────────────────────────────────────
DATA_FILE  = os.path.join("data", "submissions.json")
ROOMS_FILE = os.path.join("data", "room-assignment.json")
USERS_FILE = os.path.join("data", "users.json")

# ── Flask ─────────────────────────────────────────────────────────────────────
FLASK_SECRET   = os.environ.get("FLASK_SECRET", "dev-secret-change-in-prod")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")