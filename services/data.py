import json, os, random
from datetime import datetime
from config.config import DATA_FILE, ROOMS_FILE, USERS_FILE


# ── User accounts ─────────────────────────────────────────────────────────────

def load_users():
    """
    Loads user accounts from users.json. Returns a dict mapping email to user info:
    Parameters: None
    Returns: dict of {email: {student_id, password_hash, first_name, last_name}}
    """
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    """
    Saves user accounts to users.json. Expects a dict mapping email to user info:
    Parameters: users (dict of {email: {student_id, password_hash, first_name   
    last_name}}})
    Returns: None
    """
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ── Submissions ───────────────────────────────────────────────────────────────

def load_data():
    """
    Loads quiz session submissions from submissions.json. Returns a list of submission dicts.
    Each submission dict contains keys like id, studentName, courseCode, examName, facultyName,
    notes, status, room, staffName, checkInTime, checkOutTime.
    Parameters: None
    Returns: list of submission dicts
    """
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    """
    Saves quiz session submissions to submissions.json. Expects a list of submission dicts.
    Parameters: data (list of submission dicts)
    Returns: None
    """
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Rooms ─────────────────────────────────────────────────────────────────────

def load_rooms():
    """
    Loads room information from room-assignment.json. Returns a list of room dicts.
    Each room dict contains keys like id, type (general/aadr/reduced), capacity, staffed.
    Parameters: None
    Returns: list of room dicts
    """
    if not os.path.exists(ROOMS_FILE):
        return []
    with open(ROOMS_FILE) as f:
        return json.load(f)

def save_rooms(rooms):
    """
    Saves room information to room-assignment.json. Expects a list of room dicts.
    Parameters: rooms (list of room dicts)
    Returns: None
    """
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f, indent=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_time(iso_str):
    """
    Formats an ISO datetime string into a more readable format like "Sep 15, 2024 at 02:30 PM".
    If the input is None or empty, returns "N/A". If parsing fails, returns the original string.
    Parameters: iso_str (string in ISO datetime format, e.g. "2024-
    09-15T14:30:00")
    Returns: formatted string like "Sep 15, 2024 at 02:30 PM
    """
    if not iso_str:
        return "N/A"
    try:
        dt   = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str


def auto_assign_room(submission):
    """
    Automatically assigns a room based on the accommodation notes and current occupancy.
    Parameters: submission (dict containing at least the "notes" key for accommodation)
    Returns: room_id (string) or None if no suitable room is available
    """
    rooms = load_rooms()
    data  = load_data()

    print(f"[room] accommodation='{submission.get('notes')}' rooms loaded: {len(rooms)}")

    occupant_count = {}
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1

    accommodation = (submission.get("notes") or "").lower()

    if "aadr" in accommodation:
        target_type = "aadr"
    elif "reduced" in accommodation:
        target_type = "reduced"
    else:
        target_type = "general"

    print(f"[room] target_type='{target_type}'")

    candidates = [
        r for r in rooms
        if r.get("staffed", False) and r.get("type", "").lower() == target_type
    ]
    print(f"[room] candidates={[r['id'] for r in candidates]}")

    if not candidates:
        return None

    min_occupants = min(occupant_count.get(r["id"], 0) for r in candidates)
    least_busy    = [r for r in candidates if occupant_count.get(r["id"], 0) == min_occupants]
    return random.choice(least_busy)["id"]