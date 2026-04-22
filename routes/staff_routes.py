from flask import Blueprint, render_template

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")


@staff_bp.route("/staff-rooms")
def staff_rooms_page():
    return render_template("staff_rooms.html")


@staff_bp.route("/analytics")
def analytics_page():
    return render_template("professor_analytics.html")