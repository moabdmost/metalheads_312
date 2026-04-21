function $(id) { return document.getElementById(id); }

let qr = null;

/**
 * renders a QR code based on the provided text input. 
 * @param {*} text 
 * @returns (void) Renders a QR code based on the provided text input. 
 * It creates a new QRCode instance and appends a label showing the QR 
 * contents below the generated code.
 */

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
/**
 * Synchronizes the input field with the selected preset value and 
 * renders the QR code based on the current input.
 * @param : None
 * @returns : None
 */

function syncInputFromPreset() {
  const sid = $("sid");
  const preset = $("preset");
  if (!sid || !preset) return;

  sid.value = preset.value;
}

// Professor search and course selection logic for the staff interface. This includes
// a live search dropdown for professors and dynamic course loading based on the 
// selected professor.
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