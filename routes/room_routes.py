from flask import Blueprint, request, jsonify
from services.data import load_data, load_rooms, save_rooms


# ── Rooms ─────────────────────────────────────────────────────────────────────

# Blueprint for room-related routes, with URL prefix /rooms
rooms_bp = Blueprint("rooms", __name__, url_prefix="/api")

@rooms_bp.route("/rooms", methods=["GET"])
def get_rooms():
    """
    API endpoint to retrieve all available rooms. Returns a JSON list of room records.
    Parameters: None
    Returns: JSON list of room records, where each record is a dict containing keys like id, capacity, staffed, etc.
    """
    rooms = load_rooms()
    data  = load_data()
    occupant_count = {}
    # Iterate through all submissions and count how many are currently occupying each room.
    for s in data:
        if s["status"] in ("VERIFIED", "IN_PROGRESS", "LEAVING") and s.get("room"):
            occupant_count[s["room"]] = occupant_count.get(s["room"], 0) + 1
    # Add occupant count and availability status to each room record before returning.
    for r in rooms:
        r["occupants"] = occupant_count.get(r["id"], 0)
        r["available"] = r["occupants"] < r.get("capacity", 1)
        r.setdefault("staffed", False)

    return jsonify(rooms)


@rooms_bp.route("/rooms/<room_id>", methods=["PATCH"])
def update_room(room_id):
    """
    API endpoint to update room information, such as staffing status. Expects a JSON body with updatable fields like staffed.
    Parameters: room_id (string) - the unique ID of the room to update; None
    Returns: JSON object with the updated room record if found and updated, or an error message.
    """
    rooms = load_rooms()
    # Find the room by ID and return a 404 error if not found.
    room  = next((r for r in rooms if r["id"] == room_id), None)
    if not room:
        return jsonify({"error": "Room not found"}), 404
    # Update only allowed fields from the request body to prevent unintended changes.
    updates = request.json or {}
    if "staffed" in updates:
        room["staffed"] = bool(updates["staffed"])

    save_rooms(rooms)
    return jsonify(room)