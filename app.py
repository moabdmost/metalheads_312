from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import random
import string
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

DATA_FILE      = os.path.join("data", "submissions.json")
SUBS_COPY_FILE = os.path.join("data", "subs_copy.json")
USERS_FILE     = os.path.join("data", "users.json")

# ── Gmail config ──────────────────────────────────────────────────────────────
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "noreplyDCQC@gmail.com"
SMTP_PASSWORD = "atau irjm wtqb rrwf"   # ← REPLACE: Google Account → Security → App Passwords
# ─────────────────────────────────────────────────────────────────────────────

# ── In-memory token store ─────────────────────────────────────────────────────
# Stores { email: { code, expires_at } }
# Lives only while Flask is running — clears on restart which is fine.
reset_tokens = {}
# ─────────────────────────────────────────────────────────────────────────────


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_subs_copy():
    # Fall back to submissions.json if subs_copy.json doesn't exist
    path = SUBS_COPY_FILE if os.path.exists(SUBS_COPY_FILE) else DATA_FILE
    with open(path, "r") as f:
        return json.load(f)

def save_subs_copy(data):
    # Save to whichever file is being used
    path = SUBS_COPY_FILE if os.path.exists(SUBS_COPY_FILE) else DATA_FILE
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def fmt_time(iso_str):
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str


# ── Email helper ──────────────────────────────────────────────────────────────

def send_email(to_address, subject, plain, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = to_address
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_address, msg.as_string())
        print(f"[email] Sent to {to_address}")
        return True
    except Exception as e:
        print(f"[email] Gmail SMTP error: {e}")
        return False


# ── Completion receipt email ──────────────────────────────────────────────────

def send_completion_email(submission):
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
Exam      : {submission['examName']}
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
    <p class="greeting">Hi <strong style="color:#e8eaf6">{name}</strong>, your exam session has been marked <strong style="color:#3ecf8e">COMPLETED</strong>. Here is your official receipt.</p>
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
      <div class="detail-row"><span class="label">Submission ID</span><span class="value" style="font-family:monospace;color:#7c5cfc">{submission['id']}</span></div>
    </div>
  </div>
  <div class="footer">Questions? Contact the Quiz Center.<br/>Davidson College — Quiz Center Exam Management System</div>
</div>
</body>
</html>
"""
    send_email(student_email, subject, plain, html)


# ── API: Signup ───────────────────────────────────────────────────────────────

@app.route("/api/signup", methods=["POST"])
def signup():
    body       = request.json or {}
    email      = (body.get("email") or "").strip().lower()
    student_id = (body.get("studentId") or "").strip()
    password   = body.get("password", "")
    first_name = (body.get("firstName") or "").strip()
    last_name  = (body.get("lastName") or "").strip()

    if not all([email, student_id, password, first_name, last_name]):
        return jsonify({"error": "All fields required"}), 400

    users = load_users()
    if email in users:
        return jsonify({"error": "Account already exists"}), 409

    users[email] = {
        "student_id": student_id,
        "password":   generate_password_hash(password),
        "first_name": first_name,
        "last_name":  last_name
    }
    save_users(users)
    print(f"[signup] New account created for {email}")
    return jsonify({"message": "Account created successfully"})


# ── API: Student login ────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    body       = request.json or {}
    email      = (body.get("email") or "").strip().lower()
    student_id = (body.get("studentId") or "").strip()
    password   = body.get("password", "")

    users = load_users()

    # Look up by email directly, or search by student_id
    if email:
        record = users.get(email)
    elif student_id:
        email  = next((k for k, v in users.items() if v.get("student_id") == student_id), None)
        record = users.get(email) if email else None
    else:
        return jsonify({"error": "Email or Student ID required"}), 400

    if not record:
        return jsonify({"error": "Invalid credentials"}), 404

    if not check_password_hash(record.get("password", ""), password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Stamp login_email onto matching submission so receipt knows where to send
    data = load_data()
    for submission in data:
        if submission.get("login_email") == email:
            break
        if submission.get("studentName", "").lower() == f"{record['first_name']} {record['last_name']}".lower():
            submission["login_email"] = email
            save_data(data)
            print(f"[login] {email} logged in")
            break

    return jsonify({
        "email":      email,
        "first_name": record["first_name"],
        "last_name":  record["last_name"],
        "student_id": record["student_id"]
    })


# ── API: Forgot password — Step 1: request code ───────────────────────────────

@app.route("/api/forgot-password/request", methods=["POST"])
def forgot_request():
    print("[DEBUG] forgot_request route hit!")   # ← add this
    """
    Student enters their Davidson email.
    If it exists in subs_copy.json, send a 6-digit code to that address.
    Expires in 15 minutes.
    """
    body  = request.json or {}
    email = (body.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email required"}), 400

    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Must be a @davidson.edu email"}), 400

    users  = load_users()
    record = users.get(email)

    # Always return success even if email not found — prevents email enumeration
    if record:
        code       = "".join(random.choices(string.digits, k=6))
        expires_at = datetime.now() + timedelta(minutes=15)
        reset_tokens[email] = {"code": code, "expires_at": expires_at}

        name = f"{record.get('first_name', '')} {record.get('last_name', '')}".strip() or "Student"
        subject = "Quiz Center — Password Reset Code"
        plain = f"""\
Hi {name},

Your password reset code is:

    {code}

This code expires in 15 minutes. If you did not request a password reset, ignore this email.

— Davidson College Quiz Center
"""
        html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
  body {{ margin:0; padding:0; background:#0f1117; font-family:'DM Sans',Arial,sans-serif; color:#e8eaf6; }}
  .wrapper {{ max-width:480px; margin:40px auto; background:#1a1d27; border:1px solid #2e3350; border-radius:16px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%); padding:32px 40px 24px; }}
  .header h1 {{ font-family:'Outfit',Arial,sans-serif; font-size:1.4rem; font-weight:800; color:#fff; margin:0; }}
  .header p {{ margin:6px 0 0; color:rgba(255,255,255,0.8); font-size:0.875rem; }}
  .body {{ padding:32px 40px; }}
  .intro {{ color:#b0b8d8; font-size:0.95rem; margin-bottom:28px; line-height:1.5; }}
  .code-box {{ background:#22263a; border:1px solid #2e3350; border-radius:12px; text-align:center; padding:28px 20px; margin-bottom:24px; }}
  .code {{ font-family:'Outfit',Arial,monospace; font-size:2.8rem; font-weight:800; letter-spacing:0.2em; color:#4f8ef7; }}
  .expiry {{ font-size:0.8rem; color:#7b82a8; margin-top:10px; }}
  .warning {{ font-size:0.8rem; color:#7b82a8; line-height:1.5; }}
  .footer {{ text-align:center; padding:16px 40px 28px; font-size:0.78rem; color:#4a5070; border-top:1px solid #2e3350; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>Password Reset</h1>
    <p>Davidson College Quiz Center</p>
  </div>
  <div class="body">
    <p class="intro">Hi <strong style="color:#e8eaf6">{name}</strong>, here is your password reset code:</p>
    <div class="code-box">
      <div class="code">{code}</div>
      <div class="expiry">Expires in 15 minutes</div>
    </div>
    <p class="warning">If you did not request a password reset, you can safely ignore this email. Your password will not change.</p>
  </div>
  <div class="footer">Davidson College — Quiz Center Exam Management System</div>
</div>
</body>
</html>
"""
        send_email(email, subject, plain, html)
        print(f"[reset] Code sent to {email}, expires at {expires_at.strftime('%H:%M:%S')}")

    return jsonify({"message": "If that email exists, a code has been sent."})


# ── API: Forgot password — Step 2: verify code and reset ─────────────────────

@app.route("/api/forgot-password/verify", methods=["POST"])
def forgot_verify():
    """
    Student submits the 6-digit code + new password.
    Code must match and not be expired.
    """
    body     = request.json or {}
    email    = (body.get("email") or "").strip().lower()
    code     = (body.get("code") or "").strip()
    new_pwd  = body.get("newPassword", "").strip()

    if not email or not code or not new_pwd:
        return jsonify({"error": "Missing fields"}), 400

    token = reset_tokens.get(email)

    if not token:
        return jsonify({"error": "No reset code found. Please request a new one."}), 400

    if datetime.now() > token["expires_at"]:
        del reset_tokens[email]
        return jsonify({"error": "Code has expired. Please request a new one."}), 400

    if token["code"] != code:
        return jsonify({"error": "Incorrect code. Please try again."}), 400

    # Code is valid — update the password in users.json
    users = load_users()
    if email not in users:
        return jsonify({"error": "Account not found."}), 404

    users[email]["password"] = generate_password_hash(new_pwd)
    save_users(users)

    # Clean up the used token
    del reset_tokens[email]

    print(f"[reset] Password updated for {email}")
    return jsonify({"message": "Password reset successfully."})


# ── API: Submissions ──────────────────────────────────────────────────────────

@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    return jsonify(load_data())

@app.route("/api/submissions/<id>", methods=["GET"])
def get_submission(id):
    data = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404
    return jsonify(submission)

@app.route("/api/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    data = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404

    updates = request.json
    for key in ["status", "checkOutTime", "notes"]:
        if key in updates:
            submission[key] = updates[key]

    save_data(data)

    if submission.get("status") == "COMPLETED":
        send_completion_email(submission)
        submission["login_email"] = None
        save_data(data)

    return jsonify(submission)


# ── Test email route (remove before production) ───────────────────────────────

@app.route("/api/test-email/<id>", methods=["GET"])
def test_email(id):
    data = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404
    send_completion_email(submission)
    return jsonify({"message": f"Email attempted for {id} — check terminal"})


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/student")
def student_page():
    return render_template("student.html")

@app.route("/forgot")
def forgot_page():
    return render_template("forgot.html")

@app.route("/selection")
def selection_page():
    return render_template("selection.html")

@app.route("/qr")
def qr_page():
    return render_template("qr_generate.html")

@app.route("/room_assigned")
def room_assigned_page():
    return render_template("room_assigned.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/staff_rooms")
def staff_rooms_page():
    return render_template("staff_rooms.html")

@app.route("/scan")
def scan_page():
    return render_template("scan.html")

@app.route("/analytics")
def analytics_page():
    return render_template("professor_analytics.html")


if __name__ == "__main__":
    # host="0.0.0.0" makes the server reachable from other devices on the same
    # Wi-Fi network (phones, other laptops).  Access via http://<your-ip>:5001
    app.run(host="0.0.0.0", port=5001, debug=True, use_reloader=False)
