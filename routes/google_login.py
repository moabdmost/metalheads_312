from flask import Blueprint, request, session, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from config.config import GOOGLE_CLIENT_ID

# ── Google login ──────────────────────────────────────────────────────────────

# This blueprint handles the Google login process for students.
# It verifies the token sent from the frontend,
google_bp = Blueprint("google", __name__)

@google_bp.route("/api/google-login", methods=["POST"])
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