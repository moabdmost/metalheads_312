const API_BASE = "http://127.0.0.1:5000/api";
const output = document.getElementById("output");

function show(obj) {
  output.textContent = typeof obj === "string" ? obj : JSON.stringify(obj, null, 2);
}

async function fetchSubmission(id) {
  const res = await fetch(`${API_BASE}/submissions/${encodeURIComponent(id)}`);
  if (!res.ok) throw new Error(`Not found: ${id}`);
  return res.json();
}

async function lookup(id) {
  const cleaned = id.trim();
  if (!cleaned) return show("Enter an ID like QS-0002");
  try {
    show(`Looking up ${cleaned}...`);
    const data = await fetchSubmission(cleaned);
    show(data);
  } catch (e) {
    show(`Error: ${e.message}`);
  }
}

// Manual lookup
document.getElementById("lookupBtn").addEventListener("click", () => {
  lookup(document.getElementById("manualId").value);
});

// Camera scanning
const qr = new Html5Qrcode("reader");

qr.start(
  { facingMode: "environment" },
  { fps: 10, qrbox: 250 },
  async (decodedText) => {
    // decodedText should be QS-0002
    await lookup(decodedText);
  },
  () => { /* ignore scan errors */ }
).catch((err) => {
  // If camera permissions fail, we still support manual lookup
  show(`Camera error: ${err}. Use Manual Lookup.`);
});

