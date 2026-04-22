import json, os, random
from datetime import datetime
from config import DATA_FILE, ROOMS_FILE, USERS_FILE


# ── User accounts ─────────────────────────────────────────────────────────────

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


# ── Submissions ───────────────────────────────────────────────────────────────

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


# ── Rooms ─────────────────────────────────────────────────────────────────────

def load_rooms():
    if not os.path.exists(ROOMS_FILE):
        return []
    with open(ROOMS_FILE) as f:
        return json.load(f)

def save_rooms(rooms):
    with open(ROOMS_FILE, "w") as f:
        json.dump(rooms, f, indent=2)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt_time(iso_str):
    """Format an ISO datetime string to "Sep 15, 2024 at 02:30 PM"."""
    if not iso_str:
        return "N/A"
    try:
        dt   = datetime.fromisoformat(iso_str)
        hour = dt.strftime("%I").lstrip("0") or "12"
        return dt.strftime(f"%b %d, %Y at {hour}:%M %p")
    except Exception:
        return iso_str


def auto_assign_room(submission):
    """Pick the least-occupied staffed room that matches the student's accommodation."""
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