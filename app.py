from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from flask_cors import CORS
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
import json
import os
import smtplib
import random
import qrcode

# ── Config ─────────────────────────────────────────────────────────────────────
GOOGLE_CLIENT_ID = "318874378262-do4uihbnlojtv39fm05ctcncfjkgvb4v.apps.googleusercontent.com"

SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "noreplyDCQC@gmail.com"
SMTP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")   # set env var instead of getpass

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-change-in-prod")
CORS(app)

DATA_FILE  = os.path.join("data", "submissions.json")
ROOMS_FILE = os.path.join("data", "rooms.json")

# ── Data helpers ───────────────────────────────────────────────────────────────

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
    """
    Assign the room with the fewest current occupants that is staffed
    and (if needed) has extended_time feature.
    Falls back to any staffed room if no extended room is available.
    """
    rooms = load_rooms()
    data  = load_data()

    # Count occupants per room
    occupant_count = {}
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1

    notes = (submission.get("notes") or "").lower()
    needs_extended = "extended" in notes or "aadr" in notes

    def room_score(r):
        return occupant_count.get(r["id"], 0)

    candidates = [r for r in rooms if r.get("staffed", False)]

    if needs_extended:
        extended = [r for r in candidates if "extended_time" in r.get("features", [])]
        if extended:
            candidates = extended

    candidates.sort(key=room_score)
    return candidates[0]["id"] if candidates else None

# ── Email ──────────────────────────────────────────────────────────────────────

def send_completion_email(submission):
    student_email = submission.get("login_email")
    if not student_email:
        print(f"[email] No email for {submission['id']} — skipping.")
        return

    start   = fmt_time(submission.get("checkInTime"))
    end     = fmt_time(submission.get("checkOutTime"))
    name    = submission.get("studentName", "Student")
    subject = f"Quiz Center Receipt — {submission.get('examName','Exam')} ({submission.get('courseCode','')})"

    plain = f"""Hi {name},

Your exam session at the Davidson Quiz Center has been marked COMPLETED.

Exam      : {submission.get('examName','—')}
Course    : {submission.get('courseCode','—')} - {submission.get('courseName','—')}
Professor : {submission.get('facultyName','—')}
Start     : {start}
End       : {end}
ID        : {submission['id']}

- Davidson College Quiz Center
"""

    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<style>
body{{margin:0;padding:0;background:#0f1117;font-family:'DM Sans',Arial,sans-serif;color:#e8eaf6}}
.wrap{{max-width:560px;margin:40px auto;background:#1a1d27;border:1px solid #2e3350;border-radius:16px;overflow:hidden}}
.hdr{{background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%);padding:36px 40px 28px}}
.badge{{display:inline-block;background:rgba(255,255,255,.2);color:#fff;font-size:.75rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;padding:4px 12px;border-radius:999px;margin-bottom:12px}}
.hdr h1{{font-size:1.6rem;font-weight:800;color:#fff;margin:0 0 6px}}
.hdr p{{margin:0;color:rgba(255,255,255,.8);font-size:.9rem}}
.body{{padding:32px 40px 36px}}
.card{{background:#22263a;border:1px solid #2e3350;border-radius:12px;overflow:hidden;margin-bottom:16px}}
.ct{{font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#7b82a8;padding:12px 20px 8px;border-bottom:1px solid #2e3350}}
.dr{{display:flex;padding:12px 20px;border-bottom:1px solid #2e3350}}
.dr:last-child{{border-bottom:none}}
.lbl{{width:120px;flex-shrink:0;font-size:.8rem;color:#7b82a8}}
.val{{font-size:.875rem;color:#e8eaf6;font-weight:500}}
.tg{{display:grid;grid-template-columns:1fr 1fr}}
.tc{{padding:16px 20px;border-right:1px solid #2e3350}}
.tc:last-child{{border-right:none}}
.tl{{font-size:.72rem;color:#7b82a8;text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px}}
.tv{{font-size:.95rem;font-weight:700;color:#4f8ef7}}
.ftr{{text-align:center;padding:20px 40px 32px;font-size:.8rem;color:#4a5070;border-top:1px solid #2e3350}}
</style></head><body>
<div class="wrap">
  <div class="hdr"><div class="badge">&#10003; Completed</div>
    <h1>Exam Session Receipt</h1><p>Davidson College Quiz Center</p></div>
  <div class="body">
    <p>Hi <strong>{name}</strong>, your session is <strong style="color:#3ecf8e">COMPLETED</strong>.</p>
    <div class="card"><div class="ct">Exam Details</div>
      <div class="dr"><span class="lbl">Exam</span><span class="val">{submission.get('examName','—')}</span></div>
      <div class="dr"><span class="lbl">Course</span><span class="val"><strong>{submission.get('courseCode','—')}</strong> — {submission.get('courseName','—')}</span></div>
      <div class="dr"><span class="lbl">Professor</span><span class="val">{submission.get('facultyName','—')}</span></div>
    </div>
    <div class="card"><div class="ct">Session Times</div>
      <div class="tg">
        <div class="tc"><div class="tl">Start</div><div class="tv">{start}</div></div>
        <div class="tc"><div class="tl">End</div><div class="tv">{end}</div></div>
      </div>
    </div>
    <div class="card"><div class="ct">Reference</div>
      <div class="dr"><span class="lbl">Submission ID</span>
        <span class="val" style="font-family:monospace;color:#7c5cfc">{submission['id']}</span></div>
    </div>
  </div>
  <div class="ftr">Questions? Contact the Quiz Center.<br/>Davidson College — Quiz Center</div>
</div></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = student_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as srv:
            srv.ehlo(); srv.starttls()
            srv.login(SMTP_USER, SMTP_PASSWORD)
            srv.sendmail(SMTP_USER, student_email, msg.as_string())
        print(f"[email] Sent to {student_email} for {submission['id']}")
    except Exception as e:
        print(f"[email] Error: {e}")

# ── Page routes ────────────────────────────────────────────────────────────────

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

@app.route("/scan")
def scan_page():
    return render_template("scan.html")

@app.route("/qr")
def qr_page():
    return render_template("qr_generate.html")

@app.route("/analytics")
def analytics_page():
    return render_template("professor_analytics.html")

@app.route("/status/<submission_id>")
def status_page(submission_id):
    """Student waits here after generating QR — polls for room assignment."""
    return render_template("student_status.html", submission_id=submission_id)

# ── Auth routes ────────────────────────────────────────────────────────────────

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

# ── Form / QR routes ───────────────────────────────────────────────────────────

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
    img      = qrcode.make(new_id)
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

# ── Submissions API ────────────────────────────────────────────────────────────

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
    allowed = ["status", "checkInTime", "checkOutTime", "notes", "staffName",
               "room", "studentName", "courseCode", "courseName", "examName", "facultyName"]
    for key in allowed:
        if key in updates:
            sub[key] = updates[key]

    save_data(data)

    if sub.get("status") == "COMPLETED":
        send_completion_email(sub)

    return jsonify(sub)

# ── Rooms API ──────────────────────────────────────────────────────────────────

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

# ── Debug ──────────────────────────────────────────────────────────────────────

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
    app.run(debug=True)