function $(id) { return document.getElementById(id); }

let qr = null;

function renderQRCode(text) {
  const container = $("qrcode");
  if (!container) return;

  container.innerHTML = "";

  qr = new QRCode(container, {
    text,
    width: 220,
    height: 220
  });

  const label = document.createElement("div");
  label.style.marginTop = "10px";
  label.style.fontWeight = "600";
  label.textContent = `QR contents: ${text}`;
  container.appendChild(label);
}

function syncInputFromPreset() {
  const sid = $("sid");
  const preset = $("preset");
  if (!sid || !preset) return;

  sid.value = preset.value;
}

window.addEventListener("DOMContentLoaded", () => {
  const preset = $("preset");
  const make = $("make");
  const sid = $("sid");

  if (preset) {
    preset.addEventListener("change", () => {
      syncInputFromPreset();
      renderQRCode(sid?.value?.trim());
    });
  }

  if (make) {
    make.addEventListener("click", () => {
      const id = sid?.value?.trim();
      if (!id) return alert("Please enter an ID like QS-0002");
      renderQRCode(id);
    });
  }

  if (sid) {
    renderQRCode(sid.value.trim());
  }
});