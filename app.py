import os
from flask import Flask
from flask_cors import CORS
from config.config import FLASK_SECRET
from routes.student_routes import student_bp
from routes.staff_routes import staff_bp
from routes.resetpass_routes import resetpass_bp
from routes.authorization import auth_bp
from routes.professor_routes import faculty_bp
from routes.room_routes import rooms_bp
from routes.sub_routes import submissions_bp
from routes.google_login import google_bp
from routes.qr_generation import qr_bp


# Main application setup
app = Flask(__name__)
app.secret_key = FLASK_SECRET
CORS(app)

# Register blueprints for different route groups
app.register_blueprint(student_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(resetpass_bp)
app.register_blueprint(submissions_bp)
app.register_blueprint(google_bp)
app.register_blueprint(qr_bp)


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)