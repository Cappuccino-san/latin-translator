// content.js - In-page selection overlay for Latin grammatical parsing

let overlay = null;

function showGrammarOverlay(selectedText, grammarInfo, x, y) {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.setAttribute("id", "latin-grammar-overlay");
    overlay.style.position = "fixed";
    overlay.style.border = "1px solid #2c3e50";
    overlay.style.borderRadius = "6px";
    overlay.style.backgroundColor = "#ffffff";
    overlay.style.boxShadow = "0 4px 14px rgba(0,0,0,0.25)";
    overlay.style.padding = "12px 14px";
    overlay.style.zIndex = "2147483647"; // Ensure highest z-index
    overlay.style.maxWidth = "360px";
    overlay.style.fontSize = "13px";
    overlay.style.fontFamily = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    overlay.style.lineHeight = "1.4";
    overlay.style.color = "#1a252f";
    document.body.appendChild(overlay);
  }

  // Header and content
  overlay.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding-bottom:6px; margin-bottom:8px;">
      <span style="font-weight:bold; color:#2980b9;">Latin Parse: "${escapeHtml(selectedText)}"</span>
      <button id="close-latin-overlay" style="background:none; border:none; font-size:16px; cursor:pointer; color:#7f8c8d;">&times;</button>
    </div>
    <div style="white-space:pre-wrap; font-size:12px;">${escapeHtml(grammarInfo)}</div>
  `;

  const closeButton = overlay.querySelector("#close-latin-overlay");
  if (closeButton) {
    closeButton.addEventListener("click", () => {
      overlay.style.display = "none";
    });
  }

  // Positioning near selection
  const overlayRect = overlay.getBoundingClientRect();
  let top = y + 15;
  let left = x;

  if (top + overlayRect.height > window.innerHeight) {
    top = Math.max(10, y - overlayRect.height - 15);
  }
  if (left + overlayRect.width > window.innerWidth) {
    left = Math.max(10, window.innerWidth - overlayRect.width - 15);
  }

  overlay.style.left = `${left}px`;
  overlay.style.top = `${top}px`;
  overlay.style.display = "block";
}

document.addEventListener("mouseup", (event) => {
  // If clicking inside the overlay itself, do not close or re-trigger
  if (overlay && overlay.contains(event.target)) {
    return;
  }

  const selection = window.getSelection();
  const selectedText = selection.toString().trim();

  if (selectedText.length > 0 && selectedText.length < 150) {
    chrome.runtime.sendMessage({ type: "getGrammar", text: selectedText }, (response) => {
      if (chrome.runtime.lastError) {
        console.warn("Latin Translator:", chrome.runtime.lastError.message);
        return;
      }
      if (response && response.grammar) {
        try {
          const range = selection.getRangeAt(0);
          const rect = range.getBoundingClientRect();
          showGrammarOverlay(
            selectedText,
            response.grammar,
            rect.left,
            rect.bottom
          );
        } catch (e) {
          showGrammarOverlay(selectedText, response.grammar, event.clientX, event.clientY);
        }
      }
    });
  }
});

// Close overlay on clicking outside
document.addEventListener("mousedown", (event) => {
  if (overlay && !overlay.contains(event.target)) {
    overlay.style.display = "none";
  }
});

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
