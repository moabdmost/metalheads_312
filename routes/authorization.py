from datetime import datetime
from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from services.data import load_users, save_users

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


# ── Auth ──────────────────────────────────────────────────────────────────────

@auth_bp.route("/signup", methods=["POST"])
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

@auth_bp.route("/login", methods=["POST"])
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
