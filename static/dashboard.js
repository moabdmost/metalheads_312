const API_BASE = "/api";

const rowsEl   = document.getElementById("rows");
const msgEl    = document.getElementById("msg");
const filterEl = document.getElementById("filter");

const POLL_INTERVAL = 5000;
let pollTimer = null;

// ── Helpers ───────────────────────────────────────────────────────────────────

function setMsg(text) { msgEl.textContent = text || ""; }

async function getAll() {
  const res = await fetch(`${API_BASE}/submissions`);
  if (!res.ok) throw new Error("Failed to load submissions");
  return res.json();
}

async function getRooms() {
  const res = await fetch(`${API_BASE}/rooms`);
  if (!res.ok) return [];
  return res.json();
}

async function patch(id, patchObj) {
  const res = await fetch(`${API_BASE}/submissions/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patchObj)
  });
  if (!res.ok) throw new Error(`Failed to update ${id}`);
  return res.json();
}

async function patchRoom(roomId, patchObj) {
  const res = await fetch(`${API_BASE}/rooms/${encodeURIComponent(roomId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patchObj)
  });
  if (!res.ok) throw new Error(`Failed to update room ${roomId}`);
  return res.json();
}

function fmtTime(t) {
  if (!t) return "—";
  return t.replace("T", " ");
}

const sessionProgress = {};

function getProgress(id) {
  return sessionProgress[id] || "idle";
}

function pill(status) {
  const label = status.replace(/_/g, ' ');
  return `<span class="pill" data-status="${status}">${label}</span>`;
}

function buttonsForProgress(progress, id) {
  return `
    <button data-action="verify"   data-id="${id}" ${progress !== "idle"     ? "disabled" : ""}>Verify</button>
    <button data-action="start"    data-id="${id}" ${progress !== "verified" ? "disabled" : ""}>Start</button>
    <button data-action="complete" data-id="${id}" ${progress !== "started"  ? "disabled" : ""}>Complete</button>
  `;
}

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

function roomBadge(room) {
  if (!room) return `<span class="room-badge unassigned">No Room</span>`;
  return `<span class="room-badge assigned">${room}</span>`;
}


// ── Render submissions table ───────────────────────────────────────────────────

function render(submissions) {
  rowsEl.innerHTML = "";
  const filter = filterEl.value;

  const filtered = filter === "ALL"
    ? submissions
    : submissions.filter(s => s.status === filter);

  if (filtered.length === 0) {
    rowsEl.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:32px;">No submissions match this filter.</td></tr>`;
    return;
  }

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
        <span class="muted">Staff:</span> ${s.staffName || "—"}<br>
        <span class="muted">Faculty:</span> ${s.facultyName || "—"}
      </td>
      <td>${roomBadge(s.room)}</td>
      <td style="display:flex; gap:8px; flex-wrap:wrap;">
        ${buttonsForProgress(getProgress(s.id), s.id)}
      </td>
    `;
    rowsEl.appendChild(tr);
  }
}


// ── Room panel ────────────────────────────────────────────────────────────────

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


// ── Main refresh ──────────────────────────────────────────────────────────────

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

function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => refresh(true), POLL_INTERVAL);
}

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
  try {
    setMsg(`Updating ${id}...`);

    if (action === "verify") {
      await patch(id, { status: "VERIFIED" });
      sessionProgress[id] = "verified";
    } else if (action === "start") {
      await patch(id, { status: "IN_PROGRESS" });
      sessionProgress[id] = "started";
    } else if (action === "complete") {
      const now = new Date()
        .toLocaleString('sv-SE', { timeZone: 'America/New_York' })
        .replace(' ', 'T');
      await patch(id, { status: "COMPLETED", checkOutTime: now });
      sessionProgress[id] = "completed";
    }

    await refresh();
  } catch (err) {
    setMsg(`Error: ${err.message}`);
  } finally {
    startPolling();
  }
});

document.getElementById("refresh").addEventListener("click", () => refresh());
filterEl.addEventListener("change", () => refresh());

refresh().then(startPolling);