import os
from dotenv import load_dotenv

# Load environment variables from .env (never committed to GitHub)
load_dotenv()

# Configuration
#SMTP configuration for sending emails. Using Gmail's SMTP server with an App Password.
# ── SMTP ──────────────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "noreplyDCQC@gmail.com"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")   # Gmail App Password
# Password entered once at startup — never saved to any file.
# Use a Gmail App Password (not your real password).
# Get one at: myaccount.google.com/apppasswords

# ── Data file paths ───────────────────────────────────────────────────────────

"""
All data is stored in JSON files in the "data" directory. This includes:
- submissions.json: list of all quiz session submissions with their details and status
- room-assignment.json: list of rooms with their types and staffing status
- users.json: user accounts for the signup/login system (email, student ID, hashed password, name)
"""
DATA_FILE  = os.path.join("data", "submissions.json")
ROOMS_FILE = os.path.join("data", "room-assignment.json")
USERS_FILE = os.path.join("data", "users.json")

# ── Flask ─────────────────────────────────────────────────────────────────────
FLASK_SECRET   = os.environ.get("FLASK_SECRET", "dev-secret-change-in-prod")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

