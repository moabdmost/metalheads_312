
// Encodes the submission "id" into a QR image

function $(id) { return document.getElementById(id); }

let qr = null;

function renderQRCode(text) {
  const container = $("qrcode");
  container.innerHTML = ""; // clear previous

  qr = new QRCode(container, {
    text,
    width: 220,
    height: 220
  });

  // Add label under QR
  const label = document.createElement("div");
  label.style.marginTop = "10px";
  label.style.fontWeight = "600";
  label.textContent = `QR contents: ${text}`;
  container.appendChild(label);
}

function syncInputFromPreset() {
  $("sid").value = $("preset").value;
}

$("preset").addEventListener("change", () => {
  syncInputFromPreset();
  renderQRCode($("sid").value.trim());
});

$("make").addEventListener("click", () => {
  const id = $("sid").value.trim();
  if (!id) return alert("Please enter an ID like QS-0002");
  renderQRCode(id);
});

// Initial render
renderQRCode($("sid").value.trim());
