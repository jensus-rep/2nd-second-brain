/* Second Brain — minimal client-side helpers */

// Format JSON textarea content on blur
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".textarea-json").forEach((el) => {
    el.addEventListener("blur", () => {
      try {
        const parsed = JSON.parse(el.value);
        el.value = JSON.stringify(parsed, null, 2);
      } catch (_) {
        // Leave as-is if not valid JSON
      }
    });
  });
});

// Copy to clipboard helper
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(() => {
    const btn = document.getElementById("copy-btn");
    if (btn) {
      const original = btn.textContent;
      btn.textContent = "Copied!";
      setTimeout(() => { btn.textContent = original; }, 1500);
    }
  });
}

// Import form submit via fetch (avoids full page reload)
function submitImport(formId, endpoint, resultId) {
  const form = document.getElementById(formId);
  if (!form) return;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const textarea = form.querySelector("textarea");
    let body;
    try {
      body = JSON.parse(textarea.value);
    } catch (_) {
      showResult(resultId, { ok: false, error: { code: "PARSE_ERROR", message: "Invalid JSON" } });
      return;
    }
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    showResult(resultId, data);
  });
}

function showResult(id, data) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<div class="json-block">${JSON.stringify(data, null, 2)}</div>`;
}
