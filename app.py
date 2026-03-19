from flask import Flask, jsonify, request, send_file, make_response
from flask import render_template
from flask_cors import CORS
import json
import os
import csv
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

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
    
    print(f"Login attempt - Email: {email}, ID: {student_id}")
    
    try:
        with open(LOGIN_FILE, 'r') as f:
            students = json.load(f)
        print(f"Loaded {len(students)} students from login file")
    except FileNotFoundError:
        print(f"ERROR: File not found at {LOGIN_FILE}")
        return jsonify({"error": "Login data file not found"}), 500
    
    match = None
    for student in students:
        email_match = False
        if email:
            student_email = student.get('email', '').lower()
            email_match = student_email == email
            
        id_match = False
        if student_id:
            student_id_value = str(student.get('studentId', ''))
            id_match = student_id_value == student_id
        
        password_match = student.get('password') == password
        
        if email_match or id_match:
            print(f"Checking student: {student.get('studentName')}")
            print(f"  Email match: {email_match}, ID match: {id_match}, Password match: {password_match}")
        
        if (email_match or id_match) and password_match:
            match = student
            print(f"✓ Login successful for {student.get('studentName')}")
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
        print("✗ Login failed - no matching credentials")
        return jsonify({"success": False, "error": "Invalid credentials"}), 401


def filter_submissions(submissions, course=None, status=None, start_date=None, end_date=None):
    """Filter submissions based on query parameters"""
    filtered = submissions
    
    if course:
        filtered = [s for s in filtered if s.get('courseCode') == course]
    
    if status:
        filtered = [s for s in filtered if s.get('status') == status]
    
    if start_date:
        filtered = [s for s in filtered if s.get('checkInTime', '')[:10] >= start_date]
    
    if end_date:
        filtered = [s for s in filtered if s.get('checkInTime', '')[:10] <= end_date]
    
    return filtered


@app.route("/api/export-pdf", methods=["GET"])
def export_pdf():
    """Generate comprehensive PDF report with text wrapping"""
    data = load_data()
    
    # Get filter parameters
    course = request.args.get('course')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Filter data
    filtered_data = filter_submissions(data, course, status, start_date, end_date)
    
    # Create PDF in memory - USE LANDSCAPE for more columns
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a3a5c'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Cell text style with wrapping
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=7,
        leading=8,
        alignment=TA_LEFT
    )
    
    # Title
    title = Paragraph("Quiz Center Analytics Report - Complete Data Export", title_style)
    elements.append(title)
    
    # Metadata
    meta_text = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    if course:
        meta_text += f" | Course: {course}"
    if status:
        meta_text += f" | Status: {status}"
    if start_date or end_date:
        meta_text += f" | Date Range: {start_date or 'All'} to {end_date or 'All'}"
    
    meta = Paragraph(meta_text, styles['Normal'])
    elements.append(meta)
    elements.append(Spacer(1, 0.2*inch))
    
    # Summary stats
    total = len(filtered_data)
    completed = len([s for s in filtered_data if s.get('status') == 'COMPLETED'])
    in_progress = len([s for s in filtered_data if s.get('status') == 'IN_PROGRESS'])
    pending = len([s for s in filtered_data if s.get('status') == 'PENDING'])
    verified = len([s for s in filtered_data if s.get('status') == 'VERIFIED'])
    
    summary_data = [
        ['Total', 'Completed', 'In Progress', 'Pending', 'Verified'],
        [str(total), str(completed), str(in_progress), str(pending), str(verified)]
    ]
    
    summary_table = Table(summary_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d7a9a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Main data table - ALL FIELDS with text wrapping using Paragraph objects
    # Header row
    header_style = ParagraphStyle(
        'HeaderText',
        parent=styles['Normal'],
        fontSize=8,
        leading=9,
        textColor=colors.whitesmoke,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    table_data = [[
        Paragraph('ID', header_style),
        Paragraph('Student ID', header_style),
        Paragraph('Student Name', header_style),
        Paragraph('Course', header_style),
        Paragraph('Course Name', header_style),
        Paragraph('Exam', header_style),
        Paragraph('Check-In', header_style),
        Paragraph('Check-Out', header_style),
        Paragraph('Status', header_style),
        Paragraph('Staff', header_style),
        Paragraph('Faculty', header_style),
        Paragraph('Notes', header_style)
    ]]
    
    # Data rows - wrap all text in Paragraph objects for automatic wrapping
    for sub in filtered_data:
        table_data.append([
            Paragraph(sub.get('id', ''), cell_style),
            Paragraph(sub.get('studentId', ''), cell_style),
            Paragraph(sub.get('studentName', ''), cell_style),
            Paragraph(sub.get('courseCode', ''), cell_style),
            Paragraph(sub.get('courseName', ''), cell_style),
            Paragraph(sub.get('examName', ''), cell_style),
            Paragraph(sub.get('checkInTime', '').replace('T', ' ')[:16], cell_style),
            Paragraph(sub.get('checkOutTime', '').replace('T', ' ')[:16] if sub.get('checkOutTime') else '—', cell_style),
            Paragraph(sub.get('status', '').replace('_', ' '), cell_style),
            Paragraph(sub.get('staffName', ''), cell_style),
            Paragraph(sub.get('facultyName', ''), cell_style),
            Paragraph(sub.get('notes', ''), cell_style)
        ])
    
    # Column widths for landscape orientation (10.5 inches available)
    main_table = Table(table_data, colWidths=[
        0.5*inch,   # ID
        0.75*inch,  # Student ID
        0.9*inch,   # Student Name
        0.55*inch,  # Course Code
        1.0*inch,   # Course Name
        0.85*inch,  # Exam
        0.95*inch,  # Check-In
        0.95*inch,  # Check-Out
        0.75*inch,  # Status
        0.75*inch,  # Staff
        0.75*inch,  # Faculty
        1.2*inch    # Notes
    ])
    
    main_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1d4a5e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    
    elements.append(main_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'quiz_center_complete_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf',
        mimetype='application/pdf'
    )


@app.route("/api/export-csv", methods=["GET"])
def export_csv():
    """Generate CSV export of submissions with filters"""
    data = load_data()
    
    # Get filter parameters
    course = request.args.get('course')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Filter data
    filtered_data = filter_submissions(data, course, status, start_date, end_date)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Student ID', 'Student Name', 'Course Code', 'Course Name',
        'Exam Name', 'Check-In Time', 'Check-Out Time', 'Status',
        'Staff Name', 'Faculty Name', 'Notes'
    ])
    
    # Write data
    for sub in filtered_data:
        writer.writerow([
            sub.get('id', ''),
            sub.get('studentId', ''),
            sub.get('studentName', ''),
            sub.get('courseCode', ''),
            sub.get('courseName', ''),
            sub.get('examName', ''),
            sub.get('checkInTime', ''),
            sub.get('checkOutTime', ''),
            sub.get('status', ''),
            sub.get('staffName', ''),
            sub.get('facultyName', ''),
            sub.get('notes', '')
        ])
    
    # Create response
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename=quiz_center_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response.headers['Content-Type'] = 'text/csv'
    
    return response


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

@app.route("/professor-analytics")
def professor_analytics_page():
    return render_template("professor_analytics.html")


if __name__ == "__main__":
    app.run(debug=True)
