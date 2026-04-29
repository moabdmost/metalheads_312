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

submissions_bp = Blueprint("submissions", __name__, url_prefix="/api")

# ── Submissions ───────────────────────────────────────────────────────────────

@submissions_bp.route("/submissions", methods=["GET"])
def get_submissions():
    """
    API endpoint to retrieve all quiz session submissions. Returns a JSON list of submission records.
    Parameters: None
    Returns: JSON list of submission records, where each record is a dict containing keys like id
    """
    return jsonify(load_data())


@submissions_bp.route("/submissions/<id>", methods=["GET"])
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


@submissions_bp.route("/submissions", methods=["POST"])
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


@submissions_bp.route("/submissions/<id>", methods=["PATCH"])
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