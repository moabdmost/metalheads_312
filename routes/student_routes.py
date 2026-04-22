import os, random, qrcode
from datetime import datetime
from flask import Blueprint, request, session, render_template, redirect, url_for, jsonify
from google.oauth2 import id_token
from google.auth.transport import requests as grequests
from config import GOOGLE_CLIENT_ID
from data import load_data, save_data, auto_assign_room

student_bp = Blueprint("student", __name__)


# ── Page routes ───────────────────────────────────────────────────────────────

@student_bp.route("/")
@student_bp.route("/student")
def student_page():
    return render_template("student.html")


@student_bp.route("/selection")
def selection_page():
    return render_template("selection.html",
        student_name  = session.get("student_name", ""),
        student_email = session.get("student_email", ""))


@student_bp.route("/qr")
def qr_page():
    return render_template("qr_generate.html")


@student_bp.route("/status/<submission_id>")
def status_page(submission_id):
    return render_template("room_assigned.html",
        submission_id = submission_id,
        student_name  = session.get("student_name", ""))


# ── Google login ──────────────────────────────────────────────────────────────

@student_bp.route("/api/google-login", methods=["POST"])
def google_login():
    body  = request.json or {}
    token = body.get("token", "")

    try:
        info = id_token.verify_oauth2_token(token, grequests.Request(), GOOGLE_CLIENT_ID)
    except ValueError as e:
        print(f"[google-login] Token verification failed: {e}")
        return jsonify({"error": "Invalid Google token"}), 401

    email = info.get("email", "")
    name  = info.get("name", "")

    if not email.endswith("@davidson.edu"):
        return jsonify({"error": "Please use your @davidson.edu Google account"}), 403

    session["student_name"]  = name
    session["student_email"] = email
    print(f"[google-login] {name} <{email}> authenticated")
    return jsonify({"name": name, "email": email})


# ── QR generation + QR scan ───────────────────────────────────────────────────

@student_bp.route("/qr_generate", methods=["POST"])
def qr_generate():
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

    scan_url = url_for("student.scan_redirect", submission_id=new_id, _external=True)
    img      = qrcode.make(scan_url)
    filename = f"qr_{new_id}.png"
    img.save(os.path.join("static", filename))

    return render_template("qr_generate.html",
        qr         = url_for("static", filename=filename),
        submission = new_submission,
        status_url = url_for("student.status_page", submission_id=new_id))


@student_bp.route("/scan/<submission_id>")
def scan_redirect(submission_id):
    data = load_data()
    for s in data:
        if s["id"] == submission_id:
            if s["status"] == "PENDING":
                s["status"]      = "VERIFIED"
                s["checkInTime"] = datetime.now().isoformat(timespec="seconds")
                s["room"]        = auto_assign_room(s)
            break
    save_data(data)
    return redirect("/dashboard")