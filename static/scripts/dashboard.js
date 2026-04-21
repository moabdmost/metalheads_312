const API_BASE = "/api";
const rowsEl   = document.getElementById("rows");
const msgEl    = document.getElementById("msg");
const filterEl = document.getElementById("filter");
const POLL_INTERVAL = 5000;
let pollTimer = null;


/**
 * Sets the page status message displayed above the dashboard table.
 * @param {string} text - The text to show in the status area.
 * @returns {void}
 */
function setMsg(text) { msgEl.textContent = text || ""; }

/**
 * Fetches all submissions from the backend API.
 * @param {string} id - The ID of the submission to update.
 * @param {Object} patchObj - An object containing the fields to update.    
 * @returns res.json
 */
async function getAll() {
  const res = await fetch(`${API_BASE}/submissions`);
  if (!res.ok) throw new Error("Failed to load submissions");
  return res.json();
}

/**
 * Retrieves the list of rooms from the backend API.
 * @param {void}
 * @returns {Promise<Array>} The room list, or an empty array when unavailable.
 */
async function getRooms() {
  const res = await fetch(`${API_BASE}/rooms`);
  if (!res.ok) return [];
  return res.json();
}

/**
 * Sends an update patch for a submission record.
 * @param {string} id - The submission ID being updated.
 * @param {Object} patchObj - The fields to patch on the submission.
 * @returns {Promise<Object>} The updated submission response.
 */
async function patch(id, patchObj) {
  const res = await fetch(`${API_BASE}/submissions/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patchObj)
  });
  if (!res.ok) throw new Error(`Failed to update ${id}`);
  return res.json();
}

/**
 * Sends a PATCH request to update a room's status.
 * @param {string} roomId - The ID of the room to update.
 * @param {Object} patchObj - An object containing the fields to update.
 * @returns res.json
 */
async function patchRoom(roomId, patchObj) {
  const res = await fetch(`${API_BASE}/rooms/${encodeURIComponent(roomId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patchObj)
  });
  if (!res.ok) throw new Error(`Failed to update room ${roomId}`);
  return res.json();
}

/**
 * Formats a timestamp string for display, converting from 
 * ISO format to a more readable form.
 * @param {string} t - The timestamp string to format.
 * @returns {string} A formatted timestamp string, or "—" if input is falsy.
 */
function fmtTime(t) {
  if (!t) return "—";
  return t.replace("T", " ");
}

const sessionProgress = {};

/**
 * Gets the current progress status of a submission by its ID.
 * @param {string} id - The ID of the submission to check progress for.
 * @returns {string} The current progress status of the submission with the given ID, or "idle" if not found.
 */
function getProgress(id) {
  return sessionProgress[id] || "idle";
}



/**
 * Creates a rendered status pill element for a submission row.
 * @param {string} status - The submission status value to display.
 * @returns {string} HTML markup for a styled status pill.
 */
function pill(status) {
  const label = status.replace(/_/g, ' ');
  return `<span class="pill" data-status="${status}">${label}</span>`;
}

/**
 * Builds the action buttons for controlling submission progress.
 * @param {Object} s - The submission record that determines button state.
 * @returns {string} HTML for the start and complete action buttons.
 */
function buttonsForProgress(s) {
  const id     = s.id;
  const status = s.status;

  const canStart    = status === "VERIFIED";
  const canComplete = status === "IN_PROGRESS";


  return `
    <button data-action="start"    data-id="${id}" ${!canStart    ? "disabled" : ""}>Start</button>
    <button data-action="complete" data-id="${id}" ${!canComplete ? "disabled" : ""}>Complete</button>
    <button data-action="edit" data-id="${id}">Edit</button>
  `;
}

/**
 * Renders a check-in badge for submissions with a login email.
 * @param {Object} s - The submission object to inspect for login state.
 * @returns {string} HTML markup for the checked-in badge or an empty string.
 */
function loginBadge(s) {
  if (!s.login_email) return "";
  return `<span style="
    display:inline-block;
    margin-left:6px;
    padding:2px 8px;
    border-radius:999px;
    font-size:0.7rem;
    font-weight:600;
    background:rgba(62,207,142,0.12);
    color:#3ecf8e;
    border:1px solid rgba(62,207,142,0.3);
    vertical-align:middle;
  ">✓ Checked In</span>`;
}

/**
 * Returns a room assignment badge for table display.
 * @param {string|null|undefined} room - The assigned room label.
 * @returns {string} HTML markup for the room badge.
 */
function roomBadge(room) {
  if (!room) return `<span class="room-badge unassigned">No Room</span>`;
  return `<span class="room-badge assigned">${room}</span>`;
}


/**
 * Renders the dashboard table based on the current filter selection.
 * @param {Array<Object>} submissions - The list of submission records to display.
 * @returns {void}
 */
function render(submissions) {
  rowsEl.innerHTML = "";
  const filter = filterEl.value;

  const filtered = (filter === "ALL"
    ? submissions
    : submissions.filter(s => s.status === filter)).slice().reverse();

  if (filtered.length === 0) {
    rowsEl.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:32px;">No submissions match this filter.</td></tr>`;
    return;
  }
  // Render each submission as a table row with appropriate data and action buttons.
  for (const s of filtered) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>
        <b>${s.studentName || "—"}</b>${loginBadge(s)}
        <br><span class="muted">${s.studentId || "—"}</span>
      </td>
      <td><b>${s.courseCode || "—"}</b> — ${s.courseName || "—"}<br><span class="muted">${s.examName || "—"}</span></td>
      <td>In: ${fmtTime(s.checkInTime)}<br>Out: ${fmtTime(s.checkOutTime)}</td>
      <td>${pill(s.status)}</td>
      <td>
        <span class="muted">Faculty:</span> ${s.facultyName || "—"}
      </td>
      <td>${roomBadge(s.room)}</td>
      <td style="display:flex; gap:8px; flex-wrap:wrap;">
        ${buttonsForProgress(s)}
      </td>
    `;
    rowsEl.appendChild(tr);
  }
}

// Room panel rendering and interactions

/**
 * Loads room metadata and renders the room status panel.
 * This function is invoked when the room panel is expanded and when room state changes.
 * @param {void}
 * @returns {void}
 */
async function renderRoomPanel() {
  const panel = document.getElementById("room-panel");
  if (!panel) return;

  let rooms;
  try {
    rooms = await getRooms();
  } catch {
    panel.innerHTML = `<p class="muted" style="padding:16px;">Could not load rooms.</p>`;
    return;
  }

  if (!rooms.length) {
    panel.innerHTML = `<p class="muted" style="padding:16px;">No rooms found in rooms.json.</p>`;
    return;
  }

  panel.innerHTML = rooms.map(r => {
    const staffed   = r.staffed   ? "staffed"   : "unstaffed";
    const available = r.available ? "available" : "occupied";
    // Each room card displays the room name, 
    // capacity, status badges for availability and staffing, 
    // and a button to toggle staffing status.
    return `
      <div class="room-card" data-room-id="${r.id}">
        <div class="room-card-top">
          <span class="room-name">${r.name || r.id}</span>
          <span class="room-cap">Cap: ${r.capacity}</span>
        </div>
        <div class="room-card-badges">
          <span class="pill" data-status="${available === "available" ? "VERIFIED" : "IN_PROGRESS"}">
            ${available === "available" ? "Available" : "Occupied"}
          </span>
          <span class="pill" data-status="${staffed === "staffed" ? "COMPLETED" : "PENDING"}">
            ${staffed === "staffed" ? "Staffed" : "Unstaffed"}
          </span>
        </div>
        ${r.features && r.features.length ? `<div class="room-features">${r.features.map(f => `<span class="feature-tag">${f.replace(/_/g,' ')}</span>`).join("")}</div>` : ""}
        <button
          class="staff-toggle-btn"
          data-room-id="${r.id}"
          data-current="${staffed}"
        >${staffed === "staffed" ? "Mark Unstaffed" : "Mark Staffed"}</button>
      </div>
    `;
  }).join("");
}

// Toggle room panel visibility
document.getElementById("toggle-rooms")?.addEventListener("click", () => {
  const section = document.getElementById("room-section");
  const btn     = document.getElementById("toggle-rooms");
  const hidden  = section.style.display === "none" || !section.style.display;
  section.style.display = hidden ? "block" : "none";
  btn.textContent = hidden ? "▲ Hide Rooms" : "▼ Room Status";
  if (hidden) renderRoomPanel();
});

// Staff toggle button clicks (delegated)
document.getElementById("room-panel")?.addEventListener("click", async (e) => {
  const btn = e.target.closest(".staff-toggle-btn");
  if (!btn) return;

  const roomId  = btn.dataset.roomId;
  const current = btn.dataset.current;
  const newVal  = current === "staffed" ? false : true;

  btn.disabled = true;
  try {
    await patchRoom(roomId, { staffed: newVal });
    await renderRoomPanel();
  } catch (err) {
    setMsg(`Room update failed: ${err.message}`);
    btn.disabled = false;
  }
});


// Refreshing data and polling for updates
/**
 * Refreshes dashboard data from the API and updates the rendered table.
 * @param {boolean} [silent=false] - When true, suppresses the loading message.
 * @returns {Promise<void>} - A promise that resolves when the refresh is complete.
 */
async function refresh(silent = false) {
  try {
    if (!silent) setMsg("Loading...");
    const data = await getAll();
    render(data);
    const now = new Date().toLocaleTimeString();
    setMsg(`${data.length} record(s) — last updated ${now}`);
  } catch (e) {
    setMsg(`Error: ${e.message}`);
  }
}


/**
 * Starts background polling to refresh dashboard data at a fixed interval.
 * @param {void}
 * @returns {void}
 */
function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => refresh(true), POLL_INTERVAL);
}

/**
 * Stops the active polling interval used to refresh the dashboard.
 * @param {void}
 * @returns {void}
 */
function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}


// ── Action buttons (verify / start / complete) ────────────────────────────────

rowsEl.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn || !btn.dataset.action) return;

  const id     = btn.dataset.id;
  const action = btn.dataset.action;


  stopPolling();
  // Handle the action based on the button's data attributes, 
  // sending appropriate API requests.
  try {
    setMsg(`Updating ${id}...`);

    if (action === "start") {
      const now = new Date()
        .toLocaleString('sv-SE', { timeZone: 'America/New_York' })
        .replace(' ', 'T');
      await patch(id, { status: "IN_PROGRESS", checkInTime: now });

    } else if (action === "complete") {
      const now = new Date()
        .toLocaleString('sv-SE', { timeZone: 'America/New_York' })
        .replace(' ', 'T');
      await patch(id, { status: "COMPLETED", checkOutTime: now });
    } else if (action === "edit") {
      const allData = await getAll();
      const submission = allData.find(s => s.id === id);
      if (submission) openEdit(id, submission);
      return;
    }
    // After performing the action, refresh the data to reflect changes.
    await refresh();
  } catch (err) {
    setMsg(`Error: ${err.message}`);
  } finally {
    startPolling();
  }
});

document.getElementById("refresh").addEventListener("click", () => refresh());
filterEl.addEventListener("change", () => refresh());

let editingId = null;

/**
 * Opens the edit modal for a specific submission, populating the fields with existing data.
 * @param {*} id 
 * @param {*} submission 
 * @returns {void} - This function does not return a value. 
 * It updates the DOM to show the edit modal.
 */
function openEdit(id, submission) {
  editingId = id;
  document.getElementById("e-course-code").value = submission.courseCode || "";
  document.getElementById("e-course-name").value = submission.courseName || "";
  document.getElementById("e-professor").value = submission.facultyName || "";
  document.getElementById("e-room").value = submission.room || "";
  document.getElementById("edit-error").textContent = "";
  document.getElementById("edit-modal").style.display = "flex";
}

/**
 * Closes the edit modal and resets the editing state.
 * @param {void}
 * @returns {void} - This function does not return a value. 
 * It updates the DOM to hide the edit modal and reset related variables.
 */
function closeEdit() {
  document.getElementById("edit-modal").style.display = "none";
  editingId = null;
  document.getElementById("edit-error").textContent = "";
}

document.getElementById("submit-edit")?.addEventListener("click", async () => {
  // Handles the submission of edits to a submission record, 
  // sending a PATCH request with updated data.
  try {
    const courseCode = document.getElementById("e-course-code").value.trim();
    const courseName = document.getElementById("e-course-name").value.trim();
    const facultyName = document.getElementById("e-professor").value.trim();
    const room = document.getElementById("e-room").value.trim();

    if (!editingId) return;
    // Validate required fields before sending the update request.
    setMsg(`Updating ${editingId}...`);
    await patch(editingId, { courseCode, courseName, facultyName, room });
    await refresh();
    closeEdit();
  } catch (err) {
    document.getElementById("edit-error").textContent = `Error: ${err.message}`;
  }
});

const editModal = document.getElementById("edit-modal");
editModal?.addEventListener("click", (e) => {
  if (e.target === editModal) closeEdit();
});

refresh().then(startPolling);