const API_BASE = "http://127.0.0.1:5000/api";

const rowsEl   = document.getElementById("rows");
const msgEl    = document.getElementById("msg");
const filterEl = document.getElementById("filter");

// Auto-refresh every 5 seconds so the dashboard stays live.
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

// Tracks button progress per row for this session
const sessionProgress = {};

function getProgress(id) {
  return sessionProgress[id] || "idle";
}

function pill(status) {
  const label = status.replace(/_/g, ' ');
  return `<span class="pill" data-status="${status}">${label}</span>`;
}

// Green badge shown when student has logged in via student.html.
// Disappears automatically after staff marks exam COMPLETED.
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
  ">&#10003; Checked In</span>`;
}

// Verify is always available.
// Start and Complete are LOCKED until the student has checked in (login_email stamped).
// After Complete the row resets to idle so the next exam can begin fresh.
function buttonsForProgress(progress, id, checkedIn) {
  const verifyDisabled  = progress !== "idle";
  // Start requires: staff clicked Verify AND student has checked in
  const startDisabled   = progress !== "verified" || !checkedIn;
  // Complete requires: staff clicked Start AND student has checked in
  const completeDisabled = progress !== "started" || !checkedIn;

  const startTitle    = !checkedIn && progress === "verified"
    ? "Waiting for student to check in"
    : "";
  const completeTitle = !checkedIn && progress === "started"
    ? "Waiting for student to check in"
    : "";

  return `
    <button data-action="verify"   data-id="${id}"
      ${verifyDisabled   ? "disabled" : ""}>Verify</button>
    <button data-action="start"    data-id="${id}"
      ${startDisabled    ? "disabled" : ""}
      title="${startTitle}">Start</button>
    <button data-action="complete" data-id="${id}"
      ${completeDisabled ? "disabled" : ""}
      title="${completeTitle}">Complete</button>
  `;
}

function render(submissions) {
  rowsEl.innerHTML = "";
  const filter = filterEl.value;

  const filtered = filter === "ALL"
    ? submissions
    : submissions.filter(s => s.status === filter);

  for (const s of filtered) {
    const checkedIn = !!s.login_email;
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
        ${buttonsForProgress(getProgress(s.id), s.id, checkedIn)}
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

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => refresh(true), POLL_INTERVAL);
}

rowsEl.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn || btn.disabled) return;

  const id     = btn.dataset.id;
  const action = btn.dataset.action;

  // Pause polling while the action is in flight
  if (pollTimer) clearInterval(pollTimer);

  try {
    setMsg(`Updating ${id}...`);

    if (action === "verify") {
      await patch(id, { status: "VERIFIED" });
      sessionProgress[id] = "verified";

    } else if (action === "start") {
      await patch(id, { status: "IN_PROGRESS" });
      sessionProgress[id] = "started";

    } else if (action === "complete") {
      const now = new Date().toLocaleString('sv-SE', { timeZone: 'America/New_York' }).replace(' ', 'T');
      await patch(id, { status: "COMPLETED", checkOutTime: now });
      // Reset the row back to idle so it's ready for the next exam session.
      // The backend clears login_email and the Checked In badge disappears
      // on the next poll.
      delete sessionProgress[id];
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

// Initial load then start auto-polling
refresh().then(startPolling);
