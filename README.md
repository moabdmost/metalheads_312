# **Student Test-Taking Tracker**
## **Group #**: 5
### **Group Members:**
- Riana Doctor --> Scrum Master
- Frank Howden --> Product Owner
- Brian Chung --> Developer
- Mohamed Mostafa --> Developer


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
├── static/
│   ├── scripts/                 # JavaScript files (.js)
│   └── style_sheets/            # CSS stylesheets (.css)
│
├── templates/                   # HTML page templates (.html)
│   ├── dashboard.html
│   ├── professor_analytics.html
│   ├── qr_generate.html
│   ├── room_assigned.html
│   └── selection.html
│   └── staff_rooms.html
│   └── student.html
│ 
├── app.py                       # Main Flask application
├── hash.py                      # Password hashing utility
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

## Step 2 — Install Dependencies

Install dependencies with:

```bash
pip3 install -r requirements.txt
```

### Step 3 — Find Your IP Address

Before running the app, you need your local IP address. Run the following command in your terminal:

```bash
ipconfig getifaddr en0
```

### Step 4 — Run the App
Then run the app:

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

### `app.py` — Main Flask Application
This is the backbone of the entire project. It runs the local web server and handles all of the app's logic, including:

- **Routing** — maps each URL (e.g. `/student`, `/selection`, `/dashboard`) to its corresponding HTML page
- **Authentication** — verifies student login credentials against `data/users.json`
- **Session management** — keeps track of which student is logged in across pages
- **Form handling** — receives and processes the course, professor, and accommodation selections from `selection.html`
- **Room assignment logic** — determines which room to assign a student to based on their accommodations and current room availability from `data/room-assignment.json`
- **QR code generation** — triggers the creation of a unique QR code tied to the student's session
- **Data storage** — writes completed student submissions to `data/submissions.json`
- **API endpoints** — serves data to the dashboard and analytics pages for filtering and display

---

### `hash.py` — Password Hashing Utility
A simple utility script used to **securely hash passwords** before storing them in `data/users.json`. Passwords should never be stored in plain text, so this script takes a raw password and outputs a hashed version that the app can safely compare against during login.

**When to use it:** Any time you add a new user to `users.json`, run this script to generate the hashed version of their password.

Usage:

```bash
python hash.py
```

Enter your plain-text password when prompted, then copy the resulting hash into the `password` field of your user entry in `data/users.json`.

---
## Pages Overview

> The typical student flow goes: **Sign In** (`student.html`) → **Course Selection** (`selection.html`) → **QR Code** (`qr_generate.html`) → **Room Assignment** (`room_assigned.html`)

---

### `dashboard.html` — Submissions Dashboard
Displays **all student submissions** in one place. A quick overview of every check-in that has been recorded.

---

### `professor_analytics.html` — Professor Analytics
Displays all submissions with advanced filtering options:

- Filter by **class**
- Filter by **status** (Completed / In Progress)
- Filter by **time frame**

Supports exporting data as:
- **CSV**
- **PDF**

---

### `qr_generate.html` — QR Code Generation
Once a student completes the selection page, a **unique QR code is generated** and associated with that student's session. The QR code:

- Is **unique per student per session**
- Can be scanned to identify the student and pull up their associated submission details
- Serves as the student's digital check-in confirmation

---

### `room_assigned.html` — Room Assignments
Lets you view which **room a student has been assigned to** after signing in.

---

### `selection.html` — Course & Accommodation Selection
After logging in, students are brought to this page to provide details about their exam session:

- Select their **course/class**
- Select their **professor**
- Indicate any **accommodations** they have (e.g. extended time, separate room), if applicable

This information is tied to the student's submission and used to assign them to the appropriate room.

---

### `staff_rooms.html` — Staff Room Management
Allows staff to **view and toggle whether a room is staffed or not**, giving real-time visibility into room availability.

---

### `student.html` — Student Sign-In Page
The main sign-in page where students check in. Authentication is built in by default:

- **Email:** `ridoctor@davidson.edu`
- **Password:** `rianapass`
- **ID:** `801420479`

To add your own credentials:
1. Add your user entry to `data/users.json`
2. Hash your password using `hash.py`

---

## Data Files

### `data/users.json`
Stores user credentials. To add a new user, add their entry here and hash their password with `hash.py`.

### `data/room-assignment.json`
Tracks each room's **occupancy** and **room type** — either `Accommodations` or `General`.

### `data/submissions.json`
Automatically populated whenever a student signs in. Contains a log of **all student check-in entries**.



