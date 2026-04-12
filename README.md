# **Student Test-Taking Tracker**
## **Group #**: 5
### **Group Members:**
- Riana Doctor --> Scrum Master
- Frank Howden --> Product Owner
- Brian Chung --> Developer
- Mohamed Mostafa --> Developer

## Running the App

This project runs on a local server using your laptop's IP address.

## Step 1 — Install Dependencies

Install dependencies with:

```bash
pip3 install -r requirements.txt
```

### Step 2 — Find Your IP Address

Before running the app, you need your local IP address. Run the following command in your terminal:

```bash
ipconfig getifaddr en0
```

### Step 3 — Run the App
Then run the app:

```bash
python3 app.py
```

### Step 4 — Access the App

Once the server is running, open a browser and navigate to:

```
http://<your-ip>:5001
```

For example:

```
http://10.53.20.114:5001
```
---
## Pages Overview

### `student.html` — Student Sign-In Page
The main sign-in page where students check in. Authentication is built in by default:

- **Email:** `ridoctor@davidson.edu`
- **Password:** `rianapass`
- **ID:** `801420479`

To add your own credentials:
1. Add your user entry to `data/users.json`
2. Hash your password using `hash.py`


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

### `room_assigned.html` — Room Assignments
Lets you view which **room a student has been assigned to** after signing in.

---

### `staff_rooms.html` — Staff Room Management
Allows staff to **view and toggle whether a room is staffed or not**, giving real-time visibility into room availability.

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

## Data Files

### `data/users.json`
Stores user credentials. To add a new user, add their entry here and hash their password with `hash.py`.

### `data/room-assignment.json`
Tracks each room's **occupancy** and **room type** — either `Accommodations` or `General`.

### `data/submissions.json`
Automatically populated whenever a student signs in. Contains a log of **all student check-in entries**.



