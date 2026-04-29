import os, random, qrcode
from datetime import datetime
from flask import Blueprint, request, session, render_template, redirect, url_for
from services.data import load_data, save_data, auto_assign_room

# ── QR generation + QR scan ───────────────────────────────────────────────────

# This blueprint handles the route for generating a QR code when a student submits their exam details,
# as well as the route that staff access when they scan the QR code. 
# The QR code encodes a URL with the submission ID,
qr_bp = Blueprint("qr", __name__)

@qr_bp.route("/qr_generate", methods=["POST"])
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
    scan_url = url_for("qr.scan_redirect", submission_id=new_id, _external=True)
    img      = qrcode.make(scan_url)
    filename = f"qr_{new_id}.png"
    img.save(os.path.join("static", filename))
    # Render a page showing the generated QR code and session status, passing the QR 
    # code URL and submission info to the template.
    return render_template("qr_generate.html",
        qr         = url_for("static", filename=filename),
        submission = new_submission,
        status_url = url_for("student.status_page", submission_id=new_id))


@qr_bp.route("/scan/<submission_id>")
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