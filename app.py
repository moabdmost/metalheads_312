from flask import Flask, jsonify, request
from flask import render_template
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = os.path.join("data", "submissions.json")
LOGIN_FILE = os.path.join("data", "subs_copy.json")

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/api/submissions", methods=["GET"])
def get_submissions():
    return jsonify(load_data())

@app.route("/api/submissions/<id>", methods=["GET"])
def get_submission(id):
    data = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404
    return jsonify(submission)

@app.route("/api/submissions/<id>", methods=["PATCH"])
def update_submission(id):
    data = load_data()
    submission = next((s for s in data if s["id"] == id), None)
    if not submission:
        return jsonify({"error": "Not found"}), 404

    updates = request.json
    for key in ["status", "checkOutTime", "notes"]:
        if key in updates:
            submission[key] = updates[key]

    save_data(data)
    return jsonify(submission)

@app.route("/api/validate-login", methods=["POST"])
def validate_login():
    login_data = request.json
    email = login_data.get('email', '').lower().strip()
    student_id = login_data.get('studentId', '').strip()
    password = login_data.get('password', '')
    
    # Load subs_copy.json
    try:
        with open(LOGIN_FILE, 'r') as f:
            students = json.load(f)
    except FileNotFoundError:
        return jsonify({"error": "Login data file not found"}), 500
    
    match = None
    for student in students:
        email_match = email and student.get('email', '').lower() == email
        id_match = student_id and student.get('studentId') == student_id
        if (email_match or id_match) and student.get('password') == password:
            match = student
            break
    
    if match:
        return jsonify({
            "success": True,
            "student": {
                "studentId": match["studentId"],
                "studentName": match["studentName"],
                "email": match["email"]
            }
        })
    else:
        return jsonify({"success": False, "error": "Invalid credentials"}), 401


@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

@app.route("/scan")
def scan_page():
    return render_template("scan.html")

@app.route("/qr")
def qr_page():
    return render_template("qr_generate.html")

@app.route("/student")
def student_page():
    return render_template("student.html")

@app.route("/exam-selection")
def exam_selection_page():
    return render_template("exam_selection.html")

@app.route("/thankyou")
def thankyou_page():
    return render_template("thankyou.html")


if __name__ == "__main__":
    app.run(debug=True)
