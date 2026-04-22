import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
from data import load_data, fmt_time


def send_completion_email(submission):
    """Send a receipt email to the student when their session is marked COMPLETED."""
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
  body {{ margin:0; padding:0; background:#0f1117; font-family:'DM Sans',Arial,sans-serif; color:#e8eaf6; }}
  .wrapper {{ max-width:560px; margin:40px auto; background:#1a1d27; border:1px solid #2e3350; border-radius:16px; overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,#4f8ef7 0%,#7c5cfc 100%); padding:36px 40px 28px; }}
  .badge {{ display:inline-block; background:rgba(255,255,255,0.2); color:#fff; font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; padding:4px 12px; border-radius:999px; margin-bottom:12px; }}
  .header h1 {{ font-family:'Outfit',Arial,sans-serif; font-size:1.6rem; font-weight:800; color:#fff; margin:0 0 6px; letter-spacing:-0.02em; }}
  .header p {{ margin:0; color:rgba(255,255,255,0.8); font-size:0.9rem; }}
  .body {{ padding:32px 40px 36px; }}
  .greeting {{ font-size:1rem; color:#b0b8d8; margin-bottom:24px; line-height:1.5; }}
  .card {{ background:#22263a; border:1px solid #2e3350; border-radius:12px; overflow:hidden; margin-bottom:16px; }}
  .card-title {{ font-family:'Outfit',Arial,sans-serif; font-size:0.7rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#7b82a8; padding:12px 20px 8px; border-bottom:1px solid #2e3350; }}
  .detail-row {{ display:flex; padding:12px 20px; border-bottom:1px solid #2e3350; align-items:flex-start; }}
  .detail-row:last-child {{ border-bottom:none; }}
  .label {{ width:120px; flex-shrink:0; font-size:0.8rem; color:#7b82a8; padding-top:1px; }}
  .value {{ font-size:0.875rem; color:#e8eaf6; font-weight:500; flex:1; }}
  .times-grid {{ display:grid; grid-template-columns:1fr 1fr; }}
  .time-cell {{ padding:16px 20px; border-right:1px solid #2e3350; }}
  .time-cell:last-child {{ border-right:none; }}
  .time-label {{ font-size:0.72rem; color:#7b82a8; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px; }}
  .time-value {{ font-family:'Outfit',Arial,sans-serif; font-size:0.95rem; font-weight:700; color:#4f8ef7; }}
  .footer {{ text-align:center; padding:20px 40px 32px; font-size:0.8rem; color:#4a5070; border-top:1px solid #2e3350; line-height:1.6; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <div class="badge">&#10003; Completed</div>
    <h1>Exam Session Receipt</h1>
    <p>Davidson College Quiz Center</p>
  </div>
  <div class="body">
    <p class="greeting">
      Hi <strong style="color:#e8eaf6">{name}</strong>,
      your exam session has been marked <strong style="color:#3ecf8e">COMPLETED</strong>.
      Here is your official receipt.
    </p>
    <div class="card">
      <div class="card-title">Exam Details</div>
      <div class="detail-row"><span class="label">Exam</span><span class="value">{submission['examName']}</span></div>
      <div class="detail-row"><span class="label">Course</span><span class="value"><strong>{submission['courseCode']}</strong> — {submission['courseName']}</span></div>
      <div class="detail-row"><span class="label">Professor</span><span class="value">{submission['facultyName']}</span></div>
      <div class="detail-row"><span class="label">Proctored by</span><span class="value">{submission['staffName']}</span></div>
    </div>
    <div class="card">
      <div class="card-title">Session Times</div>
      <div class="times-grid">
        <div class="time-cell"><div class="time-label">Start Time</div><div class="time-value">{start}</div></div>
        <div class="time-cell"><div class="time-label">End Time</div><div class="time-value">{end}</div></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Reference</div>
      <div class="detail-row">
        <span class="label">Submission ID</span>
        <span class="value" style="font-family:monospace;color:#7c5cfc">{sub_id}</span>
      </div>
    </div>
  </div>
  <div class="footer">
    Questions? Contact the Quiz Center.<br/>
    Davidson College — Quiz Center Exam Management System
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

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, student_email, msg.as_string())
        print(f"[email] Receipt sent to {student_email} for {submission['id']}")
    except Exception as e:
        print(f"[email] Gmail SMTP error: {e}")