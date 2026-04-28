import os
from flask import Flask
from flask_cors import CORS
from config.config import FLASK_SECRET
from routes.student_routes import student_bp
from routes.staff_routes import staff_bp
from routes.api_routes import api_bp

# Main application setup
app = Flask(__name__)
app.secret_key = FLASK_SECRET
CORS(app)

# Register blueprints for different route groups
app.register_blueprint(student_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(api_bp)

if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5001)