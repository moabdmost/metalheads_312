from flask import Blueprint, render_template

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/dashboard")
def dashboard_page():
    """
    Renders the staff dashboard page where proctors can see the list of upcoming and active quiz sessions,
    manage room assignments, and access analytics.
    Parameters: None
    Returns: Rendered HTML page for staff dashboard with quiz session management features
    """
    return render_template("dashboard.html")


@staff_bp.route("/staff-rooms")
def staff_rooms_page():
    """
    Renders the staff rooms page where proctors can view and manage room assignments for quiz sessions.
    Parameters: None
    Returns: Rendered HTML page for staff rooms management
    """

    return render_template("staff_rooms.html")


@staff_bp.route("/analytics")
def analytics_page():
    """
    Renders the analytics page where staff can view data visualizations and insights about quiz sessions,
    such as session durations, room usage, and completion rates.
    Parameters: None
    Returns: Rendered HTML page for staff analytics and data visualization
    """
    return render_template("professor_analytics.html")