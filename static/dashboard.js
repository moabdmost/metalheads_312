const API_BASE = "http://127.0.0.1:5000/api";

const rowsEl  = document.getElementById("rows");
const msgEl   = document.getElementById("msg");
const filterEl = document.getElementById("filter");

// Auto-poll interval in milliseconds — dashboard stays live without manual refresh
const POLL_INTERVAL = 5000;
let pollTimer = null;

function setMsg(text) { msgEl.textContent = text || ""; }

async function getAll() {
  const res = await fetch(`${API_BASE}/submissions`);
  if (!res.ok) throw new Error("Failed to load submissions");
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

function fmtTime(t) {
  if (!t) return "—";
  return t.replace("T", " ");
}

// Tracks button progress per row — persists across auto-refreshes this session
const sessionProgress = {};

function getProgress(id) {
  return sessionProgress[id] || "idle"; // idle → verified → started → completed
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

// Badge shown next to the student name when they have logged in
// login_email is stamped on the submission by /api/login when the student signs in
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

function render(submissions) {
  rowsEl.innerHTML = "";
  const filter = filterEl.value;

  const filtered = filter === "ALL"
    ? submissions
    : submissions.filter(s => s.status === filter);

  for (const s of filtered) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${s.id}</td>
      <td>
        <b>${s.studentName}</b>${loginBadge(s)}
        <br><span class="muted">${s.studentId}</span>
      </td>
      <td><b>${s.courseCode}</b> — ${s.courseName}<br>${s.examName}</td>
      <td>In: ${fmtTime(s.checkInTime)}<br>Out: ${fmtTime(s.checkOutTime)}</td>
      <td>${pill(s.status)}</td>
      <td>Staff: ${s.staffName}<br>Faculty: ${s.facultyName}</td>
      <td style="display:flex; gap:8px; flex-wrap:wrap;">
        ${buttonsForProgress(getProgress(s.id), s.id)}
      </td>
    `;
    rowsEl.appendChild(tr);
  }
}

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

// Start auto-polling — silent so it doesn't flash "Loading..." every 5 seconds
function startPolling() {
  stopPolling();
  pollTimer = setInterval(() => refresh(true), POLL_INTERVAL);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

rowsEl.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;

  const id     = btn.dataset.id;
  const action = btn.dataset.action;

  // Stop polling while we process the action so they don't race
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
      const now = new Date().toISOString().slice(0, 19);
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

// Initial load then start polling
refresh().then(startPolling);
