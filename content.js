// content.js
let overlay;

function showGrammarOverlay(text, grammarInfo, x, y) {
  if (!overlay) {
    overlay = document.createElement("div");
    overlay.setAttribute("id", "latin-grammar-overlay");
    // Basic styling, can be enhanced via injected CSS or more JS styling
    overlay.style.position = "fixed";
    overlay.style.border = "1px solid black";
    overlay.style.backgroundColor = "white";
    overlay.style.padding = "10px";
    overlay.style.zIndex = "10000"; // Ensure it's on top
    overlay.style.maxWidth = "300px";
    overlay.style.fontSize = "12px";
    overlay.style.fontFamily = "sans-serif";
    document.body.appendChild(overlay);

    // Close button
    const closeButton = document.createElement("button");
    closeButton.textContent = "Close";
    closeButton.style.display = "block";
    closeButton.style.marginTop = "5px";
    closeButton.style.cursor = "pointer";
    closeButton.addEventListener("click", () => {
      if (overlay) {
        overlay.style.display = "none";
      }
    });
    overlay.appendChild(closeButton);
  }

  // Update content and position
  overlay.innerHTML = `<strong>${text}</strong>:<br>${grammarInfo.replace(/\n/g, "<br>")}`;
  const closeButton = overlay.querySelector("button"); // Re-add close button if innerHTML overwrote it
   if (!closeButton) {
        const newCloseButton = document.createElement("button");
        newCloseButton.textContent = "Close";
        newCloseButton.style.display = "block";
        newCloseButton.style.marginTop = "5px";
        newCloseButton.style.cursor = "pointer";
        newCloseButton.addEventListener("click", () => {
            if (overlay) {
                overlay.style.display = "none";
            }
        });
        overlay.appendChild(newCloseButton);
    } else {
        // Ensure the existing close button is at the end
        overlay.appendChild(closeButton);
    }

  // Position near the selection, ensuring it's within viewport
  const overlayRect = overlay.getBoundingClientRect();
  let top = y + 15; // Below the selection
  let left = x;

  if (top + overlayRect.height > window.innerHeight) {
    top = y - overlayRect.height - 15; // Above the selection
  }
  if (left + overlayRect.width > window.innerWidth) {
    left = window.innerWidth - overlayRect.width - 10; // Keep it in view horizontally
  }
  if (top < 0) top = 10;
  if (left < 0) left = 10;

  overlay.style.left = `${left}px`;
  overlay.style.top = `${top}px`;
  overlay.style.display = "block";
}


document.addEventListener("mouseup", function(event) {
  const selectedText = window.getSelection().toString().trim();
  if (selectedText.length > 0 && selectedText.length < 100) { // Basic check for meaningful selection
    // Check if the selection is likely Latin (very basic check for now)
    // A more sophisticated check might involve character sets or simple word patterns
    // For now, we assume any selected text could be Latin for testing purposes.
    console.log("Content script: Selected text - ", selectedText);

    chrome.runtime.sendMessage({ type: "getGrammar", text: selectedText }, function(response) {
      if (chrome.runtime.lastError) {
        console.error("Error getting grammar:", chrome.runtime.lastError.message);
        return;
      }
      if (response && response.grammar) {
        console.log("Content script: Received grammar - ", response.grammar);
        // Get selection coordinates
        const range = window.getSelection().getRangeAt(0);
        const rect = range.getBoundingClientRect();
        showGrammarOverlay(selectedText, response.grammar, rect.left + window.scrollX, rect.bottom + window.scrollY);
      } else {
        console.log("Content script: No grammar info received or error.");
      }
    });
  }
});

// Listen for clicks outside the overlay to close it
document.addEventListener("mousedown", function(event) {
  if (overlay && overlay.style.display === "block") {
    if (!overlay.contains(event.target)) {
      overlay.style.display = "none";
    }
  }
});

console.log("Latin Translator content script loaded.");

