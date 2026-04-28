import os, random, qrcode
from datetime import datetime
from flask import Blueprint, request, session, render_template, redirect, url_for, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from config import GOOGLE_CLIENT_ID
from data import load_data, save_data, auto_assign_room, load_users, save_users
from werkzeug.security import generate_password_hash, check_password_hash



student_bp = Blueprint("student", __name__)


# ── Page routes ───────────────────────────────────────────────────────────────

@student_bp.route("/")
@student_bp.route("/student")
def student_page():
    """
     Renders the student-facing page where they can log in with Google and fill 
     out the exam details form.
     Parameters: None
     Returns: Rendered HTML page for student login and exam selection
    """
    return render_template("student.html")


@student_bp.route("/selection")
def selection_page():
    """
    Renders the page where students select their professor, course, exam, and accommodations.
    Parameters: None (relies on session data for student info)
    Returns: Rendered HTML page for exam selection form
    """
    return render_template("selection.html",
        student_name  = session.get("student_name", ""),
        student_email = session.get("student_email", ""))


@student_bp.route("/qr")
def qr_page():
    """
    Renders the page that shows the generated QR code and session status 
    after a student submits their exam details.
    Parameters: None (relies on session data and query parameters for submission info)
    Returns: Rendered HTML page for QR code display and session status
    """
    return render_template("qr_generate.html")


@student_bp.route("/status/<submission_id>")
def status_page(submission_id):
    """
    Renders a status page for the student after they submit their exam details, 
    showing their current status and assigned room (if any).
    Parameters: submission_id (string) - the unique ID of the quiz session submission to 
    look up
    Returns: Rendered HTML page showing the status and room assignment for the given 
    submission ID
    """
    return render_template("room_assigned.html",
        submission_id = submission_id,
        student_name  = session.get("student_name", ""))


# ── Google login ──────────────────────────────────────────────────────────────

@student_bp.route("/api/google-login", methods=["POST"])
def google_login():
    """
    Handles the Google login process for students.
    Parameters: None (relies on JSON body for token)
    Returns: JSON response with student info or error message
    """
    body  = request.json or {}
    token = body.get("token", "")
    # Verify the token and extract user info using Google's OAuth2 API
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
    # Store the student's name and email in the session for later use
    session["student_name"]  = name
    session["student_email"] = email
    print(f"[google-login] {name} <{email}> authenticated")
    return jsonify({"name": name, "email": email})


# ── QR generation + QR scan ───────────────────────────────────────────────────

@student_bp.route("/qr_generate", methods=["POST"])
def qr_generate():
    """ Called when student submits the exam details form. Creates a new submission record with PENDING status,
    generates a QR code that encodes a URL with the submission ID, and renders a p
    age showing the QR code and status.
    Parameters: Form data containing facultyName, course, examName, 
    accommodation, and optionally studentName and studentEmail (if not in session)
    Returns: Rendered HTML page showing the generated QR code and session status
    """
    professor     = request.form.get("facultyName", "")
    course        = request.form.get("course", "")
    exam_name     = request.form.get("examName", "")
    accommodation = request.form.get("accommodation", "")
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
    # Generate a QR code that encodes a URL with the submission ID, which staff can scan to verify and assign a room.
    scan_url = url_for("student.scan_redirect", submission_id=new_id, _external=True)
    img      = qrcode.make(scan_url)
    filename = f"qr_{new_id}.png"
    img.save(os.path.join("static", filename))
    # Render a page showing the generated QR code and session status, passing the QR 
    # code URL and submission info to the template.
    return render_template("qr_generate.html",
        qr         = url_for("static", filename=filename),
        submission = new_submission,
        status_url = url_for("student.status_page", submission_id=new_id))


@student_bp.route("/scan/<submission_id>")
def scan_redirect(submission_id):
    """
    Called when staff scan the QR code. Updates the submission status to VERIFIED, assigns a room, and redirects to dashboard.
    Parameters: submission_id (string) - the unique ID of the quiz session submission to update
    Returns: Redirect to staff dashboard after updating submission status and room assignment
    """
    data = load_data()
    # Find the submission with the given ID and update its status to VERIFIED, set the check-in time, and assign a room.
    for s in data:
        if s["id"] == submission_id:
            if s["status"] == "PENDING":
                s["status"]      = "VERIFIED"
                s["checkInTime"] = datetime.now().isoformat(timespec="seconds")
                s["room"]        = auto_assign_room(s)
            break
    save_data(data)
    return redirect("/dashboard")

#  ── Reset password routes ───────────────────────────────────────────────────────────────

@student_bp.route("/reset-password", methods=["GET"])
def reset_password_page():
    """
    Renders the password reset page where students can enter a new password after clicking the reset link in their email.
    Parameters: None (relies on query parameters for token and email)
    Returns: Rendered HTML page for password reset form
    """
    token = request.args.get("token", "")
    email = request.args.get("email", "")
    return render_template("reset_password.html", token=token, email=email)

@student_bp.route("/reset-password", methods=["POST"])
def do_reset_password():
    """
    Handles the password reset form submission. Validates the token and email, updates the 
    user's password, and invalidates the reset token.
    Parameters: JSON body containing email, token, and new password
    Returns: JSON response indicating success or error message
    """
    # Extract and validate input data from the request body
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
 
    # Update the user's password and invalidate the reset token
    user["password"]    = generate_password_hash(password, method="pbkdf2:sha256")
    user["reset_token"] = None   # Invalidate after use
    save_users(users)
 
    return jsonify({"message": "Password updated. You can now sign in."}), 200

