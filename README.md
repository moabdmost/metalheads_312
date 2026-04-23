# **Student Test-Taking Tracker**
## **Group #**: 5
### **Group Members:**
- Riana Doctor → Scrum Master
- Frank Howden → Product Owner
- Brian Chung → Developer
- Mohamed Mostafa → Developer

---

## Project Structure

```
project/
│
├── data/                        # JSON data files
│   ├── users.json               # Stored user credentials (add new users here)
│   ├── room-assignment.json     # Tracks room occupancy and room type (Accommodations / General)
│   └── submissions.json         # Logs all student sign-in entries
│
├── routes/                      # Flask Blueprints (split from app.py)
│   ├── __init__.py
│   ├── student_routes.py        # Student-facing pages and QR flow
│   ├── staff_routes.py          # Staff-facing pages (dashboard, rooms, analytics)
│   └── api_routes.py            # All /api/* endpoints
│
├── static/
│   ├── scripts/                 # JavaScript files (.js)
│   └── style_sheets/            # CSS stylesheets (.css)
│
├── templates/                   # HTML page templates (.html)
│   ├── dashboard.html
│   ├── professor_analytics.html
│   ├── qr_generate.html
│   ├── room_assigned.html
│   ├── selection.html
│   ├── staff_rooms.html
│   └── student.html
│
├── app.py                       # Flask app init + blueprint registration
├── config.py                    # SMTP settings, file paths, secrets
├── email_utils.py               # Completion email logic
├── data.py                    # JSON load/save helpers + room assignment logic
├── requirements.txt             # Python dependencies
└── .gitignore                   # Git ignore rules
```

---

## Running the App

This project runs on a local server using your laptop's IP address.

### Step 1 — Create & Activate the Virtual Environment

This project uses a Python virtual environment to manage dependencies cleanly.

**Create the virtual environment** (only needs to be done once):

```bash
python3 -m venv venv
```

**Activate it** before running the app:

```bash
# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your terminal prompt, confirming it's active.

### Step 2 — Install Dependencies

```bash
pip3 install -r requirements.txt
```

### Step 3 — Find Your IP Address

Before running the app, you need your local IP address:

```bash
ipconfig getifaddr en0
```

### Step 4 — Run the App

```bash
python3 app.py
```

### Step 5 — Access the App

Once the server is running, open a browser and navigate to:

```
http://<your-ip>:5001
```

For example:

```
http://10.53.20.114:5001
```

---

## Core Files

### `app.py` — Flask App Entry Point
Creates the Flask app, registers the three route blueprints (`student_bp`, `staff_bp`, `api_bp`), and starts the server. This file is intentionally slim — all logic lives in the modules below.

---

### `config.py` — Settings & Constants
Centralises all configuration in one place:

- **SMTP settings** — Gmail host, port, user, and App Password for sending receipts
- **Data file paths** — paths to `submissions.json`, `room-assignment.json`, and `users.json`
- **Flask secrets** — `FLASK_SECRET` and `GOOGLE_CLIENT_ID` (loaded from environment variables)

When you need to change a credential or file path, this is the only file you need to touch.

---

### `data.py` — Data & Room Assignment Logic
Handles all reads and writes to the JSON data files, plus shared utilities:

- `load_data` / `save_data` — submissions
- `load_rooms` / `save_rooms` — room assignments
- `load_users` / `save_users` — user accounts
- `fmt_time` — formats ISO timestamps into human-readable strings
- `auto_assign_room` — picks the least-occupied, staffed room matching a student's accommodation type (`general`, `aadr`, or `reduced`)

---

### `email_utils.py` — Completion Email
Contains `send_completion_email`, which is called automatically when a session is marked **COMPLETED**. It looks up the student's email from the submission record and sends a styled HTML receipt via Gmail SMTP.

---

### `routes/student_routes.py` — Student-Facing Routes
Handles everything a student interacts with:

- `/student` and `/` — sign-in page
- `/selection` — course and accommodation selection form
- `/qr_generate` — processes the form, creates a submission record, and generates a QR code
- `/scan/<id>` — scanned by staff; marks the session **VERIFIED** and assigns a room
- `/status/<id>` — status waiting page shown after QR generation
- `/api/google-login` — verifies a Google ID token and stores the student's name/email in the session

---

### `routes/staff_routes.py` — Staff-Facing Routes
Renders the three staff pages:

- `/dashboard` — live view of all current sessions
- `/staff-rooms` — room staffing management
- `/analytics` — historical data and export tools

---

### `routes/api_routes.py` — REST API Endpoints
All `/api/*` endpoints consumed by the frontend JavaScript:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/signup` | Create a new student account |
| `POST` | `/api/login` | Log in with email + password |
| `GET` | `/api/submissions` | List all submissions |
| `GET` | `/api/submissions/<id>` | Get one submission |
| `POST` | `/api/submissions` | Create a submission (manual/API path) |
| `PATCH` | `/api/submissions/<id>` | Update a submission (triggers email on COMPLETED) |
| `GET` | `/api/rooms` | List all rooms with current occupancy |
| `PATCH` | `/api/rooms/<id>` | Toggle a room's staffed status |
| `GET` | `/api/test-email/<id>` | Debug: manually trigger a receipt email |

---

## Pages Overview

> The typical student flow goes: **Sign In** (`student.html`) → **Course Selection** (`selection.html`) → **QR Code** (`qr_generate.html`) → **Room Assignment** (`room_assigned.html`)

---

### `dashboard.html` — Submissions Dashboard
Displays all student submissions in one place — a live overview of every check-in that has been recorded.

---

### `professor_analytics.html` — Professor Analytics
Displays all submissions with advanced filtering options:

- Filter by **class**
- Filter by **status** (Completed / In Progress)
- Filter by **time frame**

Supports exporting data as **CSV** or **PDF**.

---

### `qr_generate.html` — QR Code Generation
Once a student completes the selection page, a unique QR code is generated and tied to that student's session. The QR code:

- Is unique per student per session
- Can be scanned by staff to verify the student and assign a room
- Serves as the student's digital check-in confirmation

---

### `room_assigned.html` — Room Assignment Status
Shows the student which room they have been assigned to after their QR code is scanned.

---

### `selection.html` — Course & Accommodation Selection
After logging in, students provide details about their exam session:

- Select their **course/class**
- Select their **professor**
- Indicate any **accommodations** (e.g. extended time, separate room), if applicable

This information is used to assign them to the appropriate room type.

---

### `staff_rooms.html` — Staff Room Management
Allows staff to view and toggle whether a room is staffed or not, giving real-time visibility into room availability.

---

### `student.html` — Student Sign-In Page
The main sign-in page. Students can log in with a Davidson Google account or with email + password credentials stored in `users.json`.

Default test account:
- **Email:** `ridoctor@davidson.edu`
- **Password:** `rianapass`

To add your own credentials:
1. Add your user entry to `data/users.json`
2. Hash your password using `hash.py`

---

## Data Files

### `data/users.json`
Stores user accounts. Each entry maps an email address to a hashed password and the user's name. To add a new user, add their entry here and hash their password with `hash.py`.

### `data/room-assignment.json`
Tracks each room's type (`general`, `aadr`, or `reduced`) and whether it is currently staffed. Room assignment logic in `models.py` uses this file to route incoming students.

### `data/submissions.json`
Automatically populated whenever a student submits the selection form. Contains a log of all student check-in entries, including their status, assigned room, check-in/check-out times, and course details.
