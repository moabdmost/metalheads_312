import json, os, smtplib, random, qrcode, re
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path


# Configuration
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "noreplyDCQC@gmail.com"
# Password entered once at startup — never saved to any file.
# Use a Gmail App Password (not your real password).
# Get one at: myaccount.google.com/apppasswords
SMTP_PASSWORD = "adct ymgm qikk kgsr"  # Gmail App Password for noreplyDCQC@gmail.com
# 


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-in-prod")
CORS(app)

DATA_FILE  = os.path.join("data", "submissions.json")
ROOMS_FILE = os.path.join("data", "room-assignment.json")
USERS_FILE = os.path.join("data", "users.json")

# Data loading/saving utilities

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_rooms():
    if not os.path.exists(ROOMS_FILE):
        return []
    with open(ROOMS_FILE) as f:
        return json.load(f)

def save_rooms(rooms):
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f, indent=2)

def fmt_time(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt   = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str

def auto_assign_room(submission):
    rooms = load_rooms()
    data  = load_data()

    print(f"[room] accommodation='{submission.get('notes')}' rooms loaded: {len(rooms)}")  # ADD THIS

    # Count current occupants per room
    occupant_count = {}
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1

    accommodation = (submission.get("notes") or "").lower()

    # Determine target room type based on accommodation
    if "aadr" in accommodation:
        target_type = "aadr"
    elif "reduced" in accommodation:
        target_type = "reduced"
    else:
        # None or Extended Time → general
        target_type = "general"

    print(f"[room] target_type='{target_type}'") 
    # Get staffed rooms of the right type
    candidates = [
        r for r in rooms
        if r.get("staffed", False)
        and r.get("type", "").lower() == target_type
    ]
    print(f"[room] candidates={[r['id'] for r in candidates]}")

    if not candidates:
        return None

    # Pick randomly among the least-occupied rooms
    min_occupants = min(occupant_count.get(r["id"], 0) for r in candidates)
    least_busy    = [r for r in candidates if occupant_count.get(r["id"], 0) == min_occupants]
    return random.choice(least_busy)["id"]
# Email sending utility

# ── Email via local Outlook app (pywin32) ─────────────────────────────────────
# This uses your already signed-in Outlook desktop app directly.
# No SMTP config, no passwords, no credentials needed.

# ── Email via local Outlook app (pywin32) ─────────────────────────────────────
# This uses your already signed-in Outlook desktop app directly.
# No SMTP config, no passwords, no credentials needed.

def load_subs_copy():
    with open(DATA_FILE, "r") as f:
        return json.load(f)
    
def send_completion_email(submission):
    """
    Look up the student's email from submission.json by submission id
    (uses the exact email from JSON so brchung2 etc. are handled correctly),
    then send a receipt through the local Outlook app.
    """
    # Get the email — prefer login_email (stamped at login), fall back to subs_copy
    student_email = submission.get("login_email")

    if not student_email:
        subs_copy = load_subs_copy()
        record = next((s for s in subs_copy if s["id"] == submission["id"]), None)
        if record:
            student_email = record.get("email")

    if not student_email:
        print(f"[email] No email found for {submission['id']} — skipping.")
        return

    start = fmt_time(submission.get("checkInTime"))
    end   = fmt_time(submission.get("checkOutTime"))
    name  = submission["studentName"]

    subject = f"Quiz Center Receipt — {submission['examName']} ({submission['courseCode']})"

    plain = f"""\
Hi {name},

Your exam session at the Davidson Quiz Center has been marked COMPLETED.

EXAM RECEIPT
------------
Course    : {submission['courseCode']} - {submission['courseName']}
Professor : {submission['facultyName']}

Start Time    : {start}
End Time      : {end}

Submission ID : {submission['id']}
Proctored by  : {submission['staffName']}

Questions? Contact the Quiz Center.

- Davidson College Quiz Center
"""

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
  body {{ margin:0; padding:0; background:#0f1117; font-family:'DM Sans',Arial,sans-serif; color:#e8eaf6; }}
  .wrapper {{ max-width:560px; margin:40px auto; background:#1a1d27; border:1px solid #2e3350; border-radius:16px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%); padding:36px 40px 28px; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,0.2); color:#fff; font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:4px 12px; border-radius:999px; margin-bottom:12px; }}
  .header h1 {{ font-family:'Outfit',Arial,sans-serif; font-size:1.6rem; font-weight:800; color:#fff; margin:0 0 6px; letter-spacing:-0.02em; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.8); font-size:0.9rem; }}
  .body {{ padding:32px 40px 36px; }}
  .greeting {{ font-size:1rem; color:#b0b8d8; margin-bottom:24px; line-height:1.5; }}
  .card {{ background:#22263a; border:1px solid #2e3350; border-radius:12px; overflow:hidden; margin-bottom:16px; }}
  .card-title {{ font-family:'Outfit',Arial,sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#7b82a8; padding:12px 20px 8px; border-bottom:1px solid #2e3350; }}
  .detail-row {{ display:flex; padding:12px 20px; border-bottom:1px solid #2e3350; align-items:flex-start; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .label {{ width:120px; flex-shrink:0; font-size:0.8rem; color:#7b82a8; padding-top:1px; }}
  .value {{ font-size:0.875rem; color:#e8eaf6; font-weight:500; flex:1; }}
  .times-grid {{ display:grid; grid-template-columns:1fr 1fr; }}
  .time-cell {{ padding:16px 20px; border-right:1px solid #2e3350; }}
  .time-cell:last-child {{ border-right:none; }}
  .time-label {{ font-size:0.72rem; color:#7b82a8; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; }}
  .time-value {{ font-family:'Outfit',Arial,sans-serif; font-size:0.95rem; font-weight:700; color:#4f8ef7; }}
  .footer {{ text-align:center; padding:20px 40px 32px; font-size:0.8rem; color:#4a5070; border-top:1px solid #2e3350; line-height:1.6; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="badge">&#10003; Completed</div>
    <h1>Exam Session Receipt</h1>
    <p>Davidson College Quiz Center</p>
  </div>
  <div class="body">
    <p class="greeting">
      Hi <strong style="color:#e8eaf6">{name}</strong>,
      your exam session has been marked <strong style="color:#3ecf8e">COMPLETED</strong>.
      Here is your official receipt.
    </p>
    <div class="card">
      <div class="card-title">Exam Details</div>
      <div class="detail-row"><span class="label">Exam</span><span class="value">{submission['examName']}</span></div>
      <div class="detail-row"><span class="label">Course</span><span class="value"><strong>{submission['courseCode']}</strong> — {submission['courseName']}</span></div>
      <div class="detail-row"><span class="label">Professor</span><span class="value">{submission['facultyName']}</span></div>
      <div class="detail-row"><span class="label">Proctored by</span><span class="value">{submission['staffName']}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Session Times</div>
      <div class="times-grid">
        <div class="time-cell"><div class="time-label">Start Time</div><div class="time-value">{start}</div></div>
        <div class="time-cell"><div class="time-label">End Time</div><div class="time-value">{end}</div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Reference</div>
      <div class="detail-row">
        <span class="label">Submission ID</span>
        <span class="value" style="font-family:monospace;color:#7c5cfc">{submission['id']}</span>
      </div>
    </div>
  </div>
  <div class="footer">
    Questions? Contact the Quiz Center.<br/>
    Davidson College — Quiz Center Exam Management System
  </div>
</div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = student_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, student_email, msg.as_string())
        print(f"[email] Receipt sent to {student_email} for {submission['id']}")
    except Exception as e:
        print(f"[email] Gmail SMTP error: {e}")



# Routes for rendering HTML pages
@app.route("/")
@app.route("/student")
def student_page():
    return render_template("student.html")

@app.route("/selection")
def selection_page():
    # Pass student info from session so the template can prefill hidden fields
    return render_template("selection.html",
        student_name  = session.get("student_name", ""),
        student_email = session.get("student_email", ""))

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/qr")
def qr_page():
    return render_template("qr_generate.html")

@app.route("/staff-rooms")
def staff_rooms_page():
    return render_template("staff_rooms.html")

@app.route("/analytics")
def analytics_page():
    return render_template("professor_analytics.html")

@app.route("/status/<submission_id>")
def status_page(submission_id):
    return render_template("room_assigned.html",
        submission_id = submission_id,
        student_name  = session.get("student_name", ""))

# API endpoints
@app.route("/api/google-login", methods=["POST"])
def google_login():
    """
    Receive the Google ID token from the frontend.
    Verify it, extract name + email, store in Flask session,
    return JSON so the frontend can redirect to /selection.
    """
    body  = request.json or {}
    token = body.get("token", "")

    try:
        info = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
    except ValueError as e:
        print(f"[google-login] Token verification failed: {e}")
        return jsonify({"error": "Invalid Google token"}), 401

    email = info.get("email", "")
    name  = info.get("name", "")

    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Please use your @davidson.edu Google account"}), 403

    # Store in server-side session so /qr_generate can read it
    session["student_name"]  = name
    session["student_email"] = email

    print(f"[google-login] {name} <{email}> authenticated")
    return jsonify({"name": name, "email": email})

# QR code generation and scanning
@app.route("/qr_generate", methods=["POST"])
def qr_generate():
    professor     = request.form.get("facultyName", "")
    course        = request.form.get("course", "")
    exam_name     = request.form.get("examName", "")
    accommodation = request.form.get("accommodation", "")

    # Student identity: prefer form hidden fields, fall back to session
    student_name  = request.form.get("studentName")  or session.get("student_name", "")
    student_email = request.form.get("studentEmail") or session.get("student_email", "")

    course_code, course_name = "", course
    if course and " - " in course:
        parts       = course.split(" - ", 1)
        course_code = parts[0].strip()
        course_name = parts[1].strip()

    new_id = "QS-" + str(random.randint(10000, 99999))

    new_submission = {
        "id":           new_id,
        "studentName":  student_name,
        "login_email":  student_email,
        "courseCode":   course_code,
        "courseName":   course_name,
        "examName":     exam_name,
        "facultyName":  professor,
        "notes":        accommodation,
        "status":       "PENDING",
        "room":         None,
        "staffName":    None,
        "checkInTime":  None,
        "checkOutTime": None,
    }

    data = load_data()
    data.append(new_submission)
    save_data(data)

    # Generate QR image
    scan_url = url_for("scan_redirect", submission_id=new_id, _external=True)
    img = qrcode.make(scan_url)
    filename = f"qr_{new_id}.png"
    filepath = os.path.join("static", filename)
    img.save(filepath)

    qr_url = url_for("static", filename=filename)
    # Redirect student to the status-waiting page
    return render_template("qr_generate.html",
        qr         = qr_url,
        submission = new_submission,
        status_url = url_for("status_page", submission_id=new_id))

@app.route("/scan/<submission_id>")
def scan_redirect(submission_id):
    """
    Called when staff scan the QR code.
    Marks VERIFIED, assigns room, redirects to dashboard.
    """
    data = load_data()
    for s in data:
        if s["id"] == submission_id:
            if s["status"] == "PENDING":   # only process once
                s["status"]      = "VERIFIED"
                s["checkInTime"] = datetime.now().isoformat(timespec="seconds")
                s["room"]        = auto_assign_room(s)
            break
    save_data(data)
    return redirect("/dashboard")

# Submissions API
@app.route("/api/submissions", methods=["POST"])
def create_submission():
    body = request.json or {}
    data = load_data()

    # Ensure ID is unique
    if any(s["id"] == body.get("id") for s in data):
        return jsonify({"error": "Duplicate ID"}), 409

    body["room"] = auto_assign_room(body)
    body["status"] = "VERIFIED"
    body["checkInTime"] = datetime.now().isoformat(timespec="seconds")

    data.append(body)
    save_data(data)
    return jsonify(body), 201


@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    return jsonify(load_data())

@app.route("/api/submissions/<id>", methods=["GET"])
def get_submission(id):
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    return jsonify(sub)

@app.route("/api/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    data = load_data()
    sub  = next((s for s in data if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404

    updates = request.json or {}
    allowed = ["status", "checkInTime", "checkOutTime", "notes",
               "room", "studentName", "courseCode", "courseName", "facultyName"]
    for key in allowed:
        if key in updates:
            sub[key] = updates[key]

    save_data(data)

    if sub.get("status") == "COMPLETED":
        send_completion_email(sub)

    return jsonify(sub)

# Rooms API

@app.route("/api/rooms", methods=["GET"])
def get_rooms():
    rooms = load_rooms()
    data  = load_data()

    occupant_count = {}
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1

    for r in rooms:
        r["occupants"] = occupant_count.get(r["id"], 0)
        r["available"] = r["occupants"] < r.get("capacity", 1)
        if "staffed" not in r:
            r["staffed"] = False

    return jsonify(rooms)

@app.route("/api/rooms/<room_id>", methods=["PATCH"])
def update_room(room_id):
    rooms = load_rooms()
    room  = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    updates = request.json or {}
    if "staffed" in updates:
        room["staffed"] = bool(updates["staffed"])

    save_rooms(rooms)
    return jsonify(room)

# ── /api/signup
@app.route("/api/signup", methods=["POST"])
def signup():
    data       = request.get_json()
    email      = (data.get("email") or "").strip().lower()
    password   = data.get("password") or ""
    first_name = (data.get("firstName") or "").strip().capitalize()
    last_name  = (data.get("lastName") or "").strip().capitalize()
 
    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Must use a @davidson.edu email."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if not first_name or not last_name:
        return jsonify({"error": "First and last name are required."}), 400
 
    users = load_users()
    if email in users:
        return jsonify({"error": "An account with that email already exists."}), 409
 
    users[email] = {
        "password":   generate_password_hash(password, method="pbkdf2:sha256"),
        "first_name": first_name,
        "last_name":  last_name,
    }
    save_users(users)
 
    session["student_email"] = email
    session["student_name"]  = f"{first_name} {last_name}"
    return jsonify({"first_name": first_name}), 201

# ── /api/login
@app.route("/api/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
 
    users = load_users()
 
    if not email or email not in users:
        return jsonify({"error": "No account found."}), 404
 
    user = users[email]
    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Incorrect password."}), 401
 
    session["student_email"] = email
    session["student_name"]  = f"{user['first_name']} {user['last_name']}"
    return jsonify({"first_name": user["first_name"]}), 200


# ── /api/forgot-password
import secrets as _secrets
 
@app.route("/api/forgot-password", methods=["POST"])
def forgot_password():
    data  = request.get_json()
    email = (data.get("email") or "").strip().lower()
 
    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Must use a @davidson.edu email."}), 400
 
    users = load_users()
 
    # Always return success so we don't reveal whether an account exists.
    if email not in users:
        return jsonify({"message": "If an account exists, a reset email has been sent."}), 200
 
    # Generate a short-lived token and store it on the user record.
    token = _secrets.token_urlsafe(32)
    users[email]["reset_token"] = token
    save_users(users)
 
    reset_url = f"https://your-domain.com/reset-password?token={token}&email={email}"
    # ↑ Replace with your real domain, or use url_for with _external=True if you have SERVER_NAME set.
 
    name = users[email].get("first_name", "Student")
 
    subject = "Davidson Quiz Center — Password Reset"
 
    plain = f"""\
Hi {name},
 
We received a request to reset the password for your Quiz Center account.
 
Click the link below to choose a new password (link expires in 1 hour):
 
{reset_url}
 
If you didn't request this, you can safely ignore this email.
 
— Davidson College Quiz Center
"""
 
    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
  body {{ margin:0; padding:0; background:#0f1117; font-family:'DM Sans',Arial,sans-serif; color:#e8eaf6; }}
  .wrapper {{ max-width:520px; margin:40px auto; background:#1a1d27; border:1px solid #2e3350; border-radius:16px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%); padding:32px 40px 24px; }}
  .header h1 {{ font-size:1.5rem; font-weight:800; color:#fff; margin:0 0 4px; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.75); font-size:0.875rem; }}
  .body {{ padding:32px 40px; }}
  .greeting {{ font-size:0.95rem; color:#b0b8d8; margin-bottom:24px; line-height:1.6; }}
  .btn {{ display:inline-block; padding:14px 32px; background:linear-gradient(135deg,#4f8ef7,#7c5cfc); color:#fff; text-decoration:none; border-radius:10px; font-weight:600; font-size:0.95rem; }}
  .btn-wrap {{ text-align:center; margin:24px 0; }}
  .note {{ font-size:0.8rem; color:#4a5070; line-height:1.6; margin-top:20px; }}
  .footer {{ text-align:center; padding:16px 40px 28px; font-size:0.78rem; color:#4a5070; border-top:1px solid #2e3350; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Reset Your Password</h1>
    <p>Davidson College Quiz Center</p>
  </div>
  <div class="body">
    <p class="greeting">Hi <strong style="color:#e8eaf6">{name}</strong>,<br/>
    We received a request to reset the password on your Quiz Center account. Click the button below to set a new one.</p>
    <div class="btn-wrap">
      <a href="{reset_url}" class="btn">Reset My Password</a>
    </div>
    <p class="note">
      If the button doesn't work, copy and paste this link into your browser:<br/>
      <span style="color:#7c5cfc;word-break:break-all">{reset_url}</span>
    </p>
    <p class="note">If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
  </div>
  <div class="footer">Davidson College — Quiz Center Exam Management System</div>
</div>
</body>
</html>
"""
 
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
 
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, email, msg.as_string())
        print(f"[forgot-password] Reset email sent to {email}")
    except Exception as e:
        print(f"[forgot-password] SMTP error: {e}")
        # Still return success — don't expose internal errors to the client.
 
    return jsonify({"message": "If an account exists, a reset email has been sent."}), 200


#reset-password endpoint

@app.route("/reset-password", methods=["GET"])
def reset_password_page():
    token = request.args.get("token", "")
    email = request.args.get("email", "")
    return render_template("reset_password.html", token=token, email=email)
 
 
@app.route("/api/reset-password", methods=["POST"])
def do_reset_password():
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    token    = (data.get("token") or "").strip()
    password = data.get("password") or ""
 
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
 
    users = load_users()
    user  = users.get(email)
 
    if not user or user.get("reset_token") != token:
        return jsonify({"error": "Invalid or expired reset link."}), 400
 
    user["password"]    = generate_password_hash(password, method="pbkdf2:sha256")
    user["reset_token"] = None   # Invalidate after use
    save_users(users)
 
    return jsonify({"message": "Password updated. You can now sign in."}), 200
 
 
# Debug endpoint to test email sending without going through the whole flow

@app.route("/api/test-email/<id>")
def test_email(id):
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    send_completion_email(sub)
    return jsonify({"message": f"Email attempted for {id}"})

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)