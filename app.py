from flask import Flask, jsonify, request, render_template, redirect, url_for
from flask_cors import CORS
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import smtplib
import getpass
import random
import qrcode

# ── Gmail config ──────────────────────────────────────────────────────────────
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "noreplyDCQC@gmail.com"
print("=" * 50)
SMTP_PASSWORD = getpass.getpass(f"Enter Gmail App Password for {SMTP_USER}: ")
print("=" * 50)
# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

DATA_FILE      = os.path.join("data", "submissions.json")
SUBS_COPY_FILE = os.path.join("data", "subs_copy.json")


# ── Data helpers ──────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_subs_copy():
    if not os.path.exists(SUBS_COPY_FILE):
        return []
    with open(SUBS_COPY_FILE, "r") as f:
        return json.load(f)

def fmt_time(iso_str):
    """'2026-02-14T09:05:00' -> 'Feb 14, 2026 at 9:05 AM'"""
    if not iso_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str


# ── Email (Gmail SMTP) ────────────────────────────────────────────────────────

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
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
  body {{ margin:0; padding:0; background:#0f1117; font-family:'DM Sans',Arial,sans-serif; color:#e8eaf6; }}
  .wrapper {{ max-width:560px; margin:40px auto; background:#1a1d27; border:1px solid #2e3350; border-radius:16px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%); padding:36px 40px 28px; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,0.2); color:#fff; font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:4px 12px; border-radius:999px; margin-bottom:12px; }}
  .header h1 {{ font-family:'Outfit',Arial,sans-serif; font-size:1.6rem; font-weight:800; color:#fff; margin:0 0 6px; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.8); font-size:0.9rem; }}
  .body {{ padding:32px 40px 36px; }}
  .greeting {{ font-size:1rem; color:#b0b8d8; margin-bottom:24px; line-height:1.5; }}
  .card {{ background:#22263a; border:1px solid #2e3350; border-radius:12px; overflow:hidden; margin-bottom:16px; }}
  .card-title {{ font-family:'Outfit',Arial,sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#7b82a8; padding:12px 20px 8px; border-bottom:1px solid #2e3350; }}
  .detail-row {{ display:flex; padding:12px 20px; border-bottom:1px solid #2e3350; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .label {{ width:120px; flex-shrink:0; font-size:0.8rem; color:#7b82a8; }}
  .value {{ font-size:0.875rem; color:#e8eaf6; font-weight:500; }}
  .times-grid {{ display:grid; grid-template-columns:1fr 1fr; }}
  .time-cell {{ padding:16px 20px; border-right:1px solid #2e3350; }}
  .time-cell:last-child {{ border-right:none; }}
  .time-label {{ font-size:0.72rem; color:#7b82a8; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; }}
  .time-value {{ font-family:'Outfit',Arial,sans-serif; font-size:0.95rem; font-weight:700; color:#4f8ef7; }}
  .footer {{ text-align:center; padding:20px 40px 32px; font-size:0.8rem; color:#4a5070; border-top:1px solid #2e3350; }}
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
  <div class="footer">Questions? Contact the Quiz Center.<br/>Davidson College — Quiz Center</div>
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


# ── Page routes ───────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/student")
def student_page():
    return render_template("student.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/selection")
def selection_page():
    return render_template("selection.html")

@app.route("/scan")
def scan_page():
    return render_template("scan.html")

@app.route("/qr")
def qr_page():
    return render_template("qr_generate.html")


# ── Form routes (original flow) ───────────────────────────────────────────────

@app.route("/submit", methods=["POST"])
def submit():
    """Student login form submission → create pending record → redirect to selection."""
    data = load_data()

    name       = request.form.get("firstName")
    email      = request.form.get("email")
    student_id = request.form.get("studentID")

    new_submission = {
        "id":          "QS-" + str(random.randint(1000, 9999)),
        "studentId":   student_id,
        "studentName": name,
        "login_email": email,
        "courseCode":  "",
        "courseName":  "",
        "examName":    "",
        "checkInTime": datetime.now().isoformat(timespec="seconds"),
        "checkOutTime": None,
        "status":      "PENDING",
        "room":        None,
        "staffName":   None,
        "facultyName": None,
        "notes":       ""
    }

    data.append(new_submission)
    save_data(data)
    return redirect("/selection")


@app.route("/qr_generate", methods=["POST"])
def qr_generate():
    """Selection form → create submission record → generate QR → show QR page."""
    professor     = request.form.get("facultyName")
    course        = request.form.get("course")          # full "CSC371 - Machine Learning" string
    accommodation = request.form.get("accommodation")
    new_id        = "QS-" + str(random.randint(1000, 9999))

    # Split "CSC371 - Machine Learning" into code + name if possible
    course_code = ""
    course_name = course or ""
    if course and " - " in course:
        parts       = course.split(" - ", 1)
        course_code = parts[0].strip()
        course_name = parts[1].strip()

    new_submission = {
        "id":          new_id,
        "studentId":   "",
        "studentName": "",
        "courseCode":  course_code,
        "courseName":  course_name,
        "examName":    "",
        "checkInTime": None,
        "checkOutTime": None,
        "status":      "PENDING",
        "room":        None,
        "staffName":   None,
        "facultyName": professor,
        "notes":       accommodation or ""
    }

    data = load_data()
    data.append(new_submission)
    save_data(data)

    # Generate QR code image
    img      = qrcode.make(new_id)
    filename = f"qr_{new_id}.png"
    filepath = os.path.join("static", filename)
    img.save(filepath)

    qr_url = url_for("static", filename=filename)
    return render_template("qr_generate.html", qr=qr_url, submission=new_submission)


@app.route("/scan/<submission_id>")
def scan_redirect(submission_id):
    """QR scan URL — mark submission VERIFIED and redirect to dashboard."""
    data = load_data()
    for s in data:
        if s["id"] == submission_id:
            s["status"]      = "VERIFIED"
            s["checkInTime"] = datetime.now().isoformat(timespec="seconds")
            break
    save_data(data)
    return redirect("/dashboard")


# ── API routes ────────────────────────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def login():
    body       = request.json or {}
    email      = (body.get("email") or "").strip().lower()
    student_id = (body.get("studentId") or "").strip()
    password   = body.get("password", "")

    subs_copy = load_subs_copy()

    match = next((
        s for s in subs_copy
        if ((email      and s.get("email", "").lower() == email) or
            (student_id and s.get("studentId") == student_id))
        and s.get("password") == password
    ), None)

    if not match:
        return jsonify({"error": "Invalid credentials"}), 401

    # Stamp login email onto the live submission record
    data = load_data()
    submission = next((s for s in data if s["id"] == match["id"]), None)
    if submission:
        submission["login_email"] = match["email"]
        save_data(data)
        print(f"[login] {match['email']} logged in — stamped on {match['id']}")

    safe = {k: v for k, v in match.items() if k != "password"}
    return jsonify(safe)


@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    return jsonify(load_data())

@app.route("/api/submissions/<id>", methods=["GET"])
def get_submission(id):
    data       = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404
    return jsonify(submission)

@app.route("/api/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    data       = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404

    updates = request.json or {}
    for key in ["status", "checkOutTime", "notes", "staffName", "room",
                "checkInTime", "studentName", "courseCode", "courseName",
                "examName", "facultyName"]:
        if key in updates:
            submission[key] = updates[key]

    save_data(data)

    if submission.get("status") == "COMPLETED":
        send_completion_email(submission)

    return jsonify(submission)


# ── Debug / test routes ───────────────────────────────────────────────────────

@app.route("/api/test-email/<id>", methods=["GET"])
def test_email(id):
    """Manually fire a receipt email for any submission ID. Remove before prod."""
    data       = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404
    send_completion_email(submission)
    return jsonify({"message": f"Email attempted for {id} — check terminal"})


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)