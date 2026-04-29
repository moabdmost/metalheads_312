from datetime import datetime
from flask import Blueprint, request, jsonify, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from services.data import load_data, save_data, load_rooms, save_rooms, load_users, save_users, auto_assign_room
from services.email_utils import send_completion_email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from services.data import load_data
import secrets as _secrets

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ── Auth ──────────────────────────────────────────────────────────────────────

@api_bp.route("/signup", methods=["POST"])
def signup():
    """
    API endpoint for student signup. Expects a JSON body with email, 
    studentId, password, firstName, and lastName.
    Parameters: None (expects JSON body with email, studentId, password, firstName, lastName)
    Returns: JSON response with first_name if successful, or error message if failed
    """
    # Validate and sanitize input
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

    # Hash the password and save the new user
    users[email] = {
        "password":   generate_password_hash(password, method="pbkdf2:sha256"),
        "first_name": first_name,
        "last_name":  last_name,
    }
    save_users(users)

    # Log the user in by setting session variables
    session["student_email"] = email
    session["student_name"]  = f"{first_name} {last_name}"
    return jsonify({"first_name": first_name}), 201

@api_bp.route("/login", methods=["POST"])
def login():
    """
    API endpoint for student login. Expects a JSON body with email or 
    studentId, and password.
    Parameters: None (expects JSON body with email or studentId, and password)
    Returns: JSON response with first_name if successful, or error message if failed
    """
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    users = load_users()
    matched_email = email if email in users else None

    if matched_email is None:
        return jsonify({"error": "No account found."}), 404

    user = users[matched_email]
    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Incorrect password."}), 401

    # Log the user in by setting session variables
    session["student_email"] = matched_email
    session["student_name"]  = f"{user['first_name']} {user['last_name']}"
    return jsonify({"first_name": user["first_name"]}), 200


# ── Submissions ───────────────────────────────────────────────────────────────

@api_bp.route("/submissions", methods=["GET"])
def get_submissions():
    """
    API endpoint to retrieve all quiz session submissions. Returns a JSON list of submission records.
    Parameters: None
    Returns: JSON list of submission records, where each record is a dict containing keys like id
    """
    return jsonify(load_data())


@api_bp.route("/submissions/<id>", methods=["GET"])
def get_submission(id):
    """
    API endpoint to retrieve a specific quiz session submission by its unique ID. 
    Returns a JSON object with the submission details if found, or an error message if not found.
    Parameters: id (string) - the unique ID of the quiz session submission to look up
    Returns: JSON object with submission details if found, or error message if not found
    """
    # Look up the submission by ID and return it, or return a 404 error if not found.
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    return jsonify(sub)


@api_bp.route("/submissions", methods=["POST"])
def create_submission():
    """
    API endpoint to create a new quiz session submission. 
    Expects a JSON body with details like studentName, courseCode, examName, facultyName, 
    and studentEmail. Automatically assigns a room, sets status to VERIFIED, and records check-in time.
    Parameters: None (expects JSON body with studentName, courseCode, examName, facultyName, and optionally studentEmail)
    Returns: JSON object with the created submission record, including assigned room and status
    """
    body = request.json or {}
    data = load_data()
    # Ensure the provided ID is unique if it's included in the request body.
    if any(s["id"] == body.get("id") for s in data):
        return jsonify({"error": "Duplicate ID"}), 409

    body["room"]        = auto_assign_room(body)
    body["status"]      = "VERIFIED"
    body["checkInTime"] = datetime.now().isoformat(timespec="seconds")
    # Generate a unique ID for the submission if not provided.
    data.append(body)
    save_data(data)
    return jsonify(body), 201


@api_bp.route("/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    """
    API endpoint to update an existing quiz session submission by its unique ID.
    Expects a JSON body with any updatable fields such as status, checkInTime, checkOutTime, notes, room, etc.
    If the submission is updated to COMPLETED, triggers an email notification to the student.
    Parameters: id (string) - the unique ID of the quiz session submission to update; None (expects JSON body with updatable fields)
    Returns: JSON object with the updated submission record if found and updated, or an error message if not found.
    """
    data = load_data()
    sub  = next((s for s in data if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    # Update only allowed fields from the request body to prevent unintended changes.
    updates = request.json or {}
    allowed = ["status", "checkInTime", "checkOutTime", "notes",
               "room", "studentName", "courseCode", "courseName", "facultyName"]
    # Only update fields that are in the allowed list and present in the request body.
    for key in allowed:
        if key in updates:
            sub[key] = updates[key]

    save_data(data)

    if sub.get("status") == "COMPLETED":
        send_completion_email(sub)

    return jsonify(sub)


# ── Rooms ─────────────────────────────────────────────────────────────────────

@api_bp.route("/rooms", methods=["GET"])
def get_rooms():
    """
    API endpoint to retrieve all available rooms. Returns a JSON list of room records.
    Parameters: None
    Returns: JSON list of room records, where each record is a dict containing keys like id, capacity, staffed, etc.
    """
    rooms = load_rooms()
    data  = load_data()
    occupant_count = {}
    # Iterate through all submissions and count how many are currently occupying each room.
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1
    # Add occupant count and availability status to each room record before returning.
    for r in rooms:
        r["occupants"] = occupant_count.get(r["id"], 0)
        r["available"] = r["occupants"] < r.get("capacity", 1)
        r.setdefault("staffed", False)

    return jsonify(rooms)


@api_bp.route("/rooms/<room_id>", methods=["PATCH"])
def update_room(room_id):
    """
    API endpoint to update room information, such as staffing status. Expects a JSON body with updatable fields like staffed.
    Parameters: room_id (string) - the unique ID of the room to update; None
    Returns: JSON object with the updated room record if found and updated, or an error message.
    """
    rooms = load_rooms()
    # Find the room by ID and return a 404 error if not found.
    room  = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    # Update only allowed fields from the request body to prevent unintended changes.
    updates = request.json or {}
    if "staffed" in updates:
        room["staffed"] = bool(updates["staffed"])

    save_rooms(rooms)
    return jsonify(room)

# ── Password Reset ─────────────────────────────────────────────────────────

@api_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    API endpoint to handle forgot password requests. Expects a JSON body with the user's email.
    If the email exists in the system, generates a reset token, saves it to the user record, 
    and sends a password reset email with a link containing the token.
    Parameters: None (expects JSON body with email)
    Returns: JSON response indicating that if an account exists, a reset email has been sent 
    (always returns 200 to avoid revealing account existence).
    """
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
 
    reset_url = url_for("student.do_reset_password", token=token, email=email, _external=True)
 
    name = users[email].get("first_name", "Student")
 
    subject = "Davidson Quiz Center — Password Reset"
    # Create both plain text and HTML versions of the email content.
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
  body {{ margin:0; padding:0; background:#FFFFFF; font-family:'DM Sans',Arial,sans-serif; color:#ffffff; }}
  .wrapper {{ max-width:520px; margin:40px auto; background:#0d0d0d; border:1px solid #1f1f1f; border-radius:16px; overflow:hidden; }}
  .header {{ background:#b30000; padding:32px 40px 24px; }}
  .header h1 {{ font-size:1.5rem; font-weight:800; color:#ffffff; margin:0 0 4px; }}
  .header p {{ margin:0; color:#f2f2f2; font-size:0.875rem; }}
  .body {{ padding:32px 40px; }}
  .greeting {{ font-size:0.95rem; color:#d9d9d9; margin-bottom:24px; line-height:1.6; }}
  .btn {{ display:inline-block; padding:14px 32px; background:#e60000; color:#ffffff; text-decoration:none; border-radius:10px; font-weight:600; font-size:0.95rem; }}
  .btn:hover {{ background:#cc0000; }}
  .btn-wrap {{ text-align:center; margin:24px 0; }}
  .note {{ font-size:0.8rem; color:#a6a6a6; line-height:1.6; margin-top:20px; }}
  .link {{ color:#ff4d4d; word-break:break-all; }}
  .footer {{ text-align:center; padding:16px 40px 28px; font-size:0.78rem; color:#808080; border-top:1px solid #1f1f1f; }}
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
 
    # Construct the email message with both plain text and HTML parts.
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))
 
    # Send the email using SMTP. Log any exceptions but still return success to avoid exposing internal errors to the client.
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


