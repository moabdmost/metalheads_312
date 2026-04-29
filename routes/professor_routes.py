# routes/faculty_routes.py
from flask import Blueprint, render_template

faculty_bp = Blueprint("faculty", __name__)

@faculty_bp.route("/analytics")
def analytics_page():
    """
    Renders the analytics page where proffesors can view data visualizations and insights about quiz sessions,
    such as session durations, room usage, and completion rates.
    Parameters: None
    Returns: Rendered HTML page professor staff analytics and data visualization
    """
    return render_template("professor_analytics.html")