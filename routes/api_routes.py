from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

from data import load_data, save_data, load_rooms, save_rooms, load_users, save_users, auto_assign_room
from email_utils import send_completion_email

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

    if any(s["id"] == body.get("id") for s in data):
        return jsonify({"error": "Duplicate ID"}), 409

    body["room"]        = auto_assign_room(body)
    body["status"]      = "VERIFIED"
    body["checkInTime"] = datetime.now().isoformat(timespec="seconds")

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
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1

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
    Returns: JSON object with the updated room record if found and updated, or an error message
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


# ── Debug ─────────────────────────────────────────────────────────────────────

@api_bp.route("/test-email/<id>")
def test_email(id):
    """
    API endpoint to test sending a completion email for a specific submission ID.
    Parameters: id (string) - the unique ID of the quiz session submission to look up
    Returns: JSON response indicating whether the email was attempted or if the submission was not found
    """
    sub = next((s for s in load_data() if s["id"] == id), None)
    if not sub:
        return jsonify({"error": "Not found"}), 404
    send_completion_email(sub)
    return jsonify({"message": f"Email attempted for {id}"})