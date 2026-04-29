from flask import Blueprint, request, jsonify, url_for
from werkzeug.security import generate_password_hash
from services.data import load_users, save_users
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from config.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
import secrets as _secrets


# ── Password Reset ─────────────────────────────────────────────────────────

# This blueprint handles API routes related to password reset functionality, 
# including requesting a password reset email and submitting a new password using a reset token.
resetpass_bp = Blueprint("resetpass", __name__, url_prefix="/api")


@resetpass_bp.route("/reset-password", methods=["POST"])
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



# ── Password Reset ─────────────────────────────────────────────────────────

@resetpass_bp.route("/forgot-password", methods=["POST"])
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
 
    reset_url = url_for("student.reset_password_page", token=token, email=email, _external=True)
 
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


