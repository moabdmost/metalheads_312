
const API_BASE = "http://127.0.0.1:5000/api";

const rowsEl = document.getElementById("rows");
const msgEl = document.getElementById("msg");
const filterEl = document.getElementById("filter");

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

function pill(status) {
  return `<span class="pill">${status}</span>`;
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
      <td><b>${s.studentName}</b><br><span class="muted">${s.studentId}</span></td>
      <td><b>${s.courseCode}</b> — ${s.courseName}<br>${s.examName}</td>
      <td>In: ${fmtTime(s.checkInTime)}<br>Out: ${fmtTime(s.checkOutTime)}</td>
      <td>${pill(s.status)}</td>
      <td>Staff: ${s.staffName}<br>Faculty: ${s.facultyName}</td>
      <td style="display:flex; gap:8px; flex-wrap:wrap;">
        <button data-action="verify" data-id="${s.id}">Verify</button>
        <button data-action="complete" data-id="${s.id}">Complete</button>
        <button data-action="start" data-id="${s.id}">Start</button>
      </td>
    `;
    rowsEl.appendChild(tr);
  }
}

async function refresh() {
  try {
    setMsg("Loading...");
    const data = await getAll();
    render(data);
    setMsg(`Loaded ${data.length} record(s).`);
  } catch (e) {
    setMsg(`Error: ${e.message}`);
  }
}

rowsEl.addEventListener("click", async (e) => {
  const btn = e.target.closest("button");
  if (!btn) return;

  const id = btn.dataset.id;
  const action = btn.dataset.action;

  try {
    setMsg(`Updating ${id}...`);

    if (action === "verify") {
      await patch(id, { status: "VERIFIED" });
    } else if (action === "complete") {
      const now = new Date().toISOString().slice(0, 19);
      await patch(id, { status: "COMPLETED", checkOutTime: now });
    } else if (action === "start") {
      await patch(id, { status: "IN_PROGRESS" });
    }

    await refresh();
  } catch (err) {
    setMsg(`Error: ${err.message}`);
  }
});

document.getElementById("refresh").addEventListener("click", refresh);
filterEl.addEventListener("change", refresh);

// Initial load
refresh();
