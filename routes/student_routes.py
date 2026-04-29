from flask import Blueprint, request, session, render_template


# ── Student page routes ───────────────────────────────────────────────────────────────

# This blueprint handles all routes related to the student-facing pages, 
# including the main page, exam selection, QR code display, and status page. 
# It also includes a route for rendering the password reset page when students 
# click the reset link in their email.
student_bp = Blueprint("student", __name__)

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
