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
#SMTP configuration for sending emails. Using Gmail's SMTP server with an App Password.
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
"""
All data is stored in JSON files in the "data" directory. This includes:
- submissions.json: list of all quiz session submissions with their details and status
- room-assignment.json: list of rooms with their types and staffing status
- users.json: user accounts for the signup/login system (email, student ID, hashed password, name)
"""
DATA_FILE  = os.path.join("data", "submissions.json")
ROOMS_FILE = os.path.join("data", "room-assignment.json")
USERS_FILE = os.path.join("data", "users.json")

# Data loading/saving utilities

def load_users():
    """
    Loads user accounts from users.json. Returns a dict mapping email to user info:
    Parameters: None
    Returns: dict of {email: {student_id, password_hash, first_name, last_name}}
    """
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    """
    Saves user accounts to users.json. Expects a dict mapping email to user info:
    Parameters: users (dict of {email: {student_id, password_hash, first_name   
    last_name}}})
    Returns: None
    """
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_data():
    """Loads quiz session submissions from submissions.json. Returns a list of submission dicts.
    Each submission dict contains keys like id, studentName, courseCode, examName, facultyName,
    notes, status, room, staffName, checkInTime, checkOutTime.
    Parameters: None
    Returns: list of submission dicts"""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    """
    Saves quiz session submissions to submissions.json. Expects a list of submission dicts.
    Parameters: data (list of submission dicts)
    Returns: None
    """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_rooms():
    """
    Loads room information from room-assignment.json. Returns a list of room dicts.
    Each room dict contains keys like id, type (general/aadr/reduced), capacity, staffed.
    Parameters: None
    Returns: list of room dicts
    """
    if not os.path.exists(ROOMS_FILE):
        return []
    with open(ROOMS_FILE) as f:
        return json.load(f)

def save_rooms(rooms):
    """Saves room information to room-assignment.json. Expects a list of room dicts.
    Parameters: rooms (list of room dicts)
    Returns: None
    """
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f, indent=2)

def fmt_time(iso_str):
    """
    formats an ISO datetime string into a more readable format like "Sep 15, 2024 at 02:30 PM".
    If the input is None or empty, returns "N/A". If parsing fails, returns the original string.
    Parameters: iso_str (string in ISO datetime format, e.g. "2024-
    09-15T14:30:00")
    Returns: formatted string like "Sep 15, 2024 at 02:30 PM
    """
    if not iso_str:
        return "N/A"
    #try to parse the ISO string and reformat it; if it fails, just return the original string
    try:
        dt   = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str

def auto_assign_room(submission):
    """
    Automatically assigns a room based on the accommodation notes and current occupancy.
    Parameters: submission (dict containing at least the "notes" key for accommodation)
    Returns: room_id (string) or None if no suitable room is available
    """
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
    """
    Loads a copy of the submissions data from submissions.json. This is used to look up 
    the student's email
    Parameters: None
    Returns: list of submission dicts
    """
    with open(DATA_FILE, "r") as f:
        return json.load(f)
    
def send_completion_email(submission):
    """
    Look up the student's email from submission.json by submission id
    (uses the exact email from JSON so brchung2 etc. are handled correctly),
    then send a receipt through the local Outlook app.
    Parameters: submission (dict containing at least "id", "studentName", "courseCode", 
    "courseName","examName", "facultyName", "staffName", "checkInTime", "checkOutTime")
    Returns: None

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

    #getting the start and end time from submissions
    start = fmt_time(submission.get("checkInTime"))
    end   = fmt_time(submission.get("checkOutTime"))
    name  = submission["studentName"]

    subject = f"Quiz Center Receipt — {submission['examName']} ({submission['courseCode']})"
    #below is the format of the email that will be sent to the student after their session is 
    # marked completed. It includes the exam details, session times, and a reference ID.
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
#details of the computer-generated HTML email template, which includes inline 
# CSS for styling and a structured layout to present the exam receipt information 
# in a visually appealing way.
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
    
    #trying to send the email using Gmail's SMTP server with TLS encryption. 
    # It logs in using the provided SMTP_USER and SMTP_PASSWORD, then sends the email 
    # to the student's email address. If there's an error during this process, 
    # it catches the exception and prints an error message.
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
    """
     Renders the student-facing page where they can log in with Google and fill 
     out the exam details form.
     Parameters: None
     Returns: Rendered HTML page for student login and exam selection
     """
    return render_template("student.html")

@app.route("/selection")
def selection_page():
    """
    Renders the page where students select their professor, course, exam, and accommodations.
     Parameters: None (relies on session data for student info)
     Returns: Rendered HTML page for exam selection form"""
    # Pass student info from session so the template can prefill hidden fields
    return render_template("selection.html",
        student_name  = session.get("student_name", ""),
        student_email = session.get("student_email", ""))

@app.route("/dashboard")
def dashboard_page():
    """Renders the staff-facing dashboard page where they can see current sessions, 
    manage rooms, and view analytics.
    Parameters: None
    Returns: Rendered HTML page for staff dashboard
    """
    return render_template("dashboard.html")

@app.route("/qr")
def qr_page():
    """Renders the page that shows the generated QR code and session status 
    after a student submits their exam details.
    Parameters: None (relies on session data and query parameters for submission info)
    Returns: Rendered HTML page for QR code display and session status"""
    return render_template("qr_generate.html")

@app.route("/staff-rooms")
def staff_rooms_page():
    """Renders the page where staff can view and manage room assignments and staffing status.
    Parameters: None
    Returns: Rendered HTML page for staff room management
    """
    return render_template("staff_rooms.html")

@app.route("/analytics")
def analytics_page():
    """
    Renders the analytics page where staff can see historical data and trends about 
    quiz sessions.
    Parameters: None
    Returns: Rendered HTML page for professor analytics and historical data"""
    return render_template("professor_analytics.html")

@app.route("/status/<submission_id>")
def status_page(submission_id):
    """Renders a status page for the student after they submit their exam details, 
    showing their current status and assigned room (if any).
    Parameters: submission_id (string) - the unique ID of the quiz session submission to 
    look up
    Returns: Rendered HTML page showing the status and room assignment for the given 
    submission ID  """
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
    Parameters: JSON body containing "token" (Google ID token string)
    Returns: JSON response with "name" and "email" if successful, or error message if failed
    """
    body  = request.json or {}
    token = body.get("token", "")

    # Verify the token using Google's library. This checks the signature, expiry, and audience.
    try:
        info = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
    except ValueError as e:
        print(f"[google-login] Token verification failed: {e}")
        return jsonify({"error": "Invalid Google token"}), 401

    email = info.get("email", "")
    name  = info.get("name", "")

    # Ensure the email is a Davidson account
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
    """Called when student submits the exam details form. Creates a new submission record with PENDING status,
    generates a QR code that encodes a URL with the submission ID, and renders a p
    age showing the QR code and status.
    Parameters: Form data containing facultyName, course, examName, 
    accommodation, and optionally studentName and studentEmail (if not in session)
    Returns: Rendered HTML page showing the generated QR code and session status"""
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
    #loading in new submission
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

    #load the data into the dashboard
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
    Parameters: submission_id (string) - the unique ID of the quiz session submission to update
    Returns: Redirect to the staff dashboard page after updating the submission status 
    and room assignment
    """
    data = load_data()
    # Find the submission by ID and update its status to VERIFIED, 
    # set check-in time, and assign a room
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
    """API endpoint to create a new quiz session submission. 
    Expects a JSON body with studentName, courseCode, courseName, examName, 
    facultyName, notes, and optionally email. Automatically assigns a unique ID, 
    sets status to VERIFIED, assigns a room based on accommodations, and 
    timestamps the check-in time. Returns the created submission as JSON.
    Parameters: JSON body containing studentName, courseCode, courseName, examName,
    facultyName, notes, and optionally email
    Returns: JSON response with the created submission record, including assigned ID,
    assigned room, and timestamps
    """
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
    """API endpoint to retrieve all quiz session submissions. 
    Returns a list of submission records as JSON.
    Parameters: None
    Returns: JSON response containing a list of all quiz session submissions,
    including their details, status, room assignments, and timestamps
    """
    return jsonify(load_data())

@app.route("/api/submissions/<id>", methods=["GET"])
def get_submission(id):
    """
    API endpoint to retrieve a specific quiz session submission by its unique ID.
    Parameters: id (string) - the unique ID of the quiz session submission to retrieve
    Returns: JSON response containing the submission record with the specified ID, 
    or an error message if"""
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    return jsonify(sub)

@app.route("/api/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    """API endpoint to update a specific quiz session submission by its unique ID.
    Expects a JSON body with any of the updatable fields: status, checkInTime,
    checkOutTime, notes, room, studentName, courseCode, courseName, facultyName.
    If the status is updated to COMPLETED, it triggers sending a completion email 
    to the student.
    Parameters: id (string) - the unique ID of the quiz session submission to update;
    JSON body containing any of the updatable fields: status, checkInTime, checkOutTime,
    notes, room, studentName, courseCode, courseName, facultyName
    Returns: JSON response containing the updated submission record, or an error 
    message if not found
    """
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
    """"
    API endpoint to retrieve all room information, including current occupancy 
    and availability status.
     Parameters: None
     Returns: JSON response containing a list of all rooms, each with its details, 
     current occupant count, and availability status based on capacity
     """
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
    """
    Updates what room the test taker is in, and whether the room is staffed. 
    This is used by staff to mark rooms as staffed/un-staffed, 
    and to move students if needed.
    Parameters: room_id (string) - the unique ID of the room to update;
    JSON body containing any of the updatable fields: staffed (boolean)
    Returns: JSON response containing the updated room record, 
    or an error message if not found
    """
    rooms = load_rooms()
    room  = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    updates = request.json or {}
    if "staffed" in updates:
        room["staffed"] = bool(updates["staffed"])

    save_rooms(rooms)
    return jsonify(room)


@app.route("/api/signup", methods=["POST"])
def signup():
    """
    API endpoint for student signup. Expects a JSON body with email, 
    studentId, password, firstName, and lastName.
    Parameters: None (expects JSON body with email, studentId, password, firstName, lastName)
    Returns: JSON response with first_name if successful, or error message if failed"""
    data       = request.get_json()
    email      = (data.get("email") or "").strip().lower()
    #student_id = (data.get("studentId") or "").strip()
    password   = data.get("password") or ""
    first_name = (data.get("firstName") or "").strip().capitalize()
    last_name  = (data.get("lastName") or "").strip().capitalize()


    """
    Validates the signup input data for email, student ID, password, and names.
    """
    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Must use a @davidson.edu email."}), 400
    #if not re.fullmatch(r'\d{9}', student_id):
        #return jsonify({"error": "Student ID must be exactly 9 digits."}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400
    if not first_name or not last_name:
        return jsonify({"error": "First and last name are required."}), 400

    users = load_users()
    if email in users:
        return jsonify({"error": "An account with that email already exists."}), 409

    users[email] = {
        #"student_id": student_id,
        "password":   generate_password_hash(password, method="pbkdf2:sha256"),
        "first_name": first_name,
        "last_name":  last_name,
    }
    """
    Saves the new user account to users.json and updates the 
    Flask session with the student's email and name.
    """
    save_users(users)

    session["student_email"] = email
    session["student_name"]  = f"{first_name} {last_name}"
    return jsonify({"first_name": first_name}), 201


@app.route("/api/login", methods=["POST"])
def login():
    """
    API endpoint for student login. Expects a JSON body with email or 
    studentId, and password.
    Parameters: None (expects JSON body with email or studentId, and password)
    Returns: JSON response with first_name if successful, or error message if failed"""
    data       = request.get_json()
    email      = (data.get("email") or "").strip().lower()
    #student_id = (data.get("studentId") or "").strip()
    password   = data.get("password") or ""

    users = load_users()

    # Find by email or student ID
    matched_email = None
    if email:
        matched_email = email if email in users else None
    #elif student_id:
        #matched_email = next(
            #(k for k, v in users.items() if v.get("student_id") == student_id), None
        #)

    if matched_email is None:
        return jsonify({"error": "No account found."}), 404

    user = users[matched_email]
    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Incorrect password."}), 401

    session["student_email"] = matched_email
    session["student_name"]  = f"{user['first_name']} {user['last_name']}"
    return jsonify({"first_name": user["first_name"]}), 200

# Debug endpoint to test email sending without going through the whole flow

@app.route("/api/test-email/<id>")
def test_email(id):
    """Debug endpoint to test the email sending functionality by submission ID.
    Parameters: id (string) - the unique ID of the quiz session submission to test email for
    Returns: JSON response indicating that the email was attempted, 
    or an error message if not found
    """
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    send_completion_email(sub)
    return jsonify({"message": f"Email attempted for {id}"})

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)