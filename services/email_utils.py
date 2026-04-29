import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from services.data import load_data, fmt_time


def send_completion_email(submission):
    """
    Send a receipt email to the student when their session is marked COMPLETED.
    Parameters: submission (dict containing keys like studentName, studentEmail, 
    examName, courseCode, facultyName, checkInTime, checkOutTime, staffName)
    Returns: None
    """
    student_email = submission.get("login_email")

    if not student_email:
        subs = load_data()
        record = next((s for s in subs if s["id"] == submission["id"]), None)
        if record:
            student_email = record.get("email")

    if not student_email:
        print(f"[email] No email found for {submission['id']} — skipping.")
        return

    start = fmt_time(submission.get("checkInTime"))
    end   = fmt_time(submission.get("checkOutTime"))
    name  = submission["studentName"]
    sub_id = submission["id"]

    subject = f"Quiz Center Receipt — {submission['examName']} ({submission['courseCode']})"

    # below is the format of the email that will be sent to the student after their session is 
    # marked completed. It includes the exam details, session times, and a reference ID.
    
    plain = f"""\
Hi {name},

Your exam session at the Davidson Quiz Center has been marked COMPLETED.


EXAM RECEIPT
------------
Course    : {submission['courseCode']} - {submission['courseName']}
Professor : {submission['facultyName']}

Start Time    : {start}
End Time      : {end}

Submission ID : {sub_id}
Proctored by  : {submission['staffName']}

Questions? Contact the Quiz Center.

- Davidson College Quiz Center
"""

    html = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800&family=DM+Sans:wght@400;500&display=swap');
  body {{ margin:0; padding:0; background:#111111; font-family:'DM Sans',Arial,sans-serif; color:#1a1a1a; }}
  .wrapper {{ max-width:560px; margin:40px auto; background:#ffffff; border:1px solid #e0e0e0; border-radius:16px; overflow:hidden; box-shadow:0 8px 40px rgba(0,0,0,0.25); }}
 
  /* ── Header ── */
  .header {{ background:linear-gradient(135deg,#c0392b 0%,#8B0000 100%); padding:36px 40px 28px; }}
  .header-top {{ display:flex; align-items:center; gap:12px; margin-bottom:16px; }}
  .logo-mark {{ width:38px; height:38px; background:rgba(255,255,255,0.15); border:1.5px solid rgba(255,255,255,0.3); border-radius:10px; display:inline-flex; align-items:center; justify-content:center; font-family:'Outfit',Arial,sans-serif; font-weight:800; font-size:13px; color:#fff; letter-spacing:-0.5px; }}
  .logo-text {{ font-family:'Outfit',Arial,sans-serif; font-weight:700; font-size:0.9rem; color:rgba(255,255,255,0.85); letter-spacing:0.02em; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,0.18); border:1px solid rgba(255,255,255,0.35); color:#fff; font-size:0.72rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; padding:4px 14px; border-radius:999px; margin-bottom:12px; }}
  .header h1 {{ font-family:'Outfit',Arial,sans-serif; font-size:1.65rem; font-weight:800; color:#fff; margin:0 0 5px; letter-spacing:-0.02em; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.72); font-size:0.875rem; }}
 
  /* ── Body ── */
  .body {{ padding:32px 40px 36px; background:#ffffff; }}
  .greeting {{ font-size:0.95rem; color:#444444; margin-bottom:24px; line-height:1.65; }}
 
  /* ── Cards ── */
  .card {{ background:#fafafa; border:1px solid #ebebeb; border-radius:12px; overflow:hidden; margin-bottom:14px; }}
  .card-title {{ font-family:'Outfit',Arial,sans-serif; font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#c0392b; padding:11px 20px 9px; border-bottom:1px solid #ebebeb; background:#fff5f5; }}
  .detail-row {{ display:flex; padding:11px 20px; border-bottom:1px solid #f2f2f2; align-items:flex-start; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .label {{ width:125px; flex-shrink:0; font-size:0.78rem; color:#999999; padding-top:1px; font-weight:500; }}
  .value {{ font-size:0.875rem; color:#1a1a1a; font-weight:600; flex:1; }}
 
  /* ── Times grid ── */
  .times-grid {{ display:grid; grid-template-columns:1fr 1fr; }}
  .time-cell {{ padding:16px 20px; border-right:1px solid #f2f2f2; }}
  .time-cell:last-child {{ border-right:none; }}
  .time-label {{ font-size:0.7rem; color:#999999; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:6px; font-weight:500; }}
  .time-value {{ font-family:'Outfit',Arial,sans-serif; font-size:0.95rem; font-weight:700; color:#c0392b; }}
 
  /* ── Footer ── */
  .footer {{ text-align:center; padding:20px 40px 28px; font-size:0.78rem; color:#aaaaaa; border-top:1px solid #eeeeee; line-height:1.7; background:#fafafa; }}
  .footer strong {{ color:#c0392b; font-weight:600; }}
</style>
</head>
<body>
<div class="wrapper">
 
  <!-- Header -->
  <div class="header">
    <div class="header-top">
      <div class="logo-mark">QC</div>
      <span class="logo-text">Davidson Quiz Center</span>
    </div>
    <div class="badge">&#10003;&nbsp; Session Completed</div>
    <h1>Exam Session Receipt</h1>
    <p>Davidson College Quiz Center</p>
  </div>
 
  <!-- Body -->
  <div class="body">
    <p class="greeting">
      Hi <strong style="color:#111111">{name}</strong>,<br/>
      your exam session has been marked <strong style="color:#c0392b">COMPLETED</strong>.
      Here is your official receipt — please keep it for your records.
    </p>
 
    <!-- Exam Details -->
    <div class="card">
      <div class="card-title">Exam Details</div>
      <div class="detail-row">
        <span class="label">Exam</span>
        <span class="value">{submission['examName']}</span>
      </div>
      <div class="detail-row">
        <span class="label">Course</span>
        <span class="value"><strong>{submission['courseCode']}</strong> &mdash; {submission['courseName']}</span>
      </div>
      <div class="detail-row">
        <span class="label">Professor</span>
        <span class="value">{submission['facultyName']}</span>
      </div>
      <div class="detail-row">
        <span class="label">Proctored by</span>
        <span class="value">{submission['staffName']}</span>
      </div>
    </div>
 
    <!-- Session Times -->
    <div class="card">
      <div class="card-title">Session Times</div>
      <div class="times-grid">
        <div class="time-cell">
          <div class="time-label">Start Time</div>
          <div class="time-value">{start}</div>
        </div>
        <div class="time-cell">
          <div class="time-label">End Time</div>
          <div class="time-value">{end}</div>
        </div>
      </div>
    </div>
 
    <!-- Reference -->
    <div class="card">
      <div class="card-title">Reference</div>
      <div class="detail-row">
        <span class="label">Submission ID</span>
        <span class="value" style="font-family:monospace;color:#c0392b;font-size:0.85rem">{sub_id}</span>
      </div>
    </div>
 
  </div>
 
  <!-- Footer -->
  <div class="footer">
    Questions? Contact the Quiz Center.<br/>
    <strong>Davidson College</strong> &mdash; Quiz Center Exam Management System
  </div>
 
</div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Davidson Quiz Center <{SMTP_USER}>"
    msg["To"]      = student_email
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html,  "html"))

    # trying to send the email using Gmail's SMTP server with TLS encryption. 
    # It logs in using the provided SMTP_USER and SMTP_PASSWORD, then sends the email 
    # to the student's email address. If there's an error during this process, 
    # it catches the exception and prints an error message.

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, student_email, msg.as_string())
        print(f"[email] Receipt sent to {student_email} for {submission['id']}")
    except Exception as e:
        print(f"[email] Gmail SMTP error: {e}")



