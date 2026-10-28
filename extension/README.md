# Browser Extension — Hooked to Latin NLP FastAPI Core

A Manifest V3 Chrome extension client connecting directly to the local Python FastAPI engine (`http://127.0.0.1:8000`).

## Architecture & Integration

- **Manifest**: Manifest V3 (`manifest.json`) requesting `activeTab`, `scripting`, `storage`, and host permissions for `http://127.0.0.1:8000/*` and `http://localhost:8000/*`.
- **Icons**: Real PNG icons (`icons/icon16.png`, `icons/icon48.png`, `icons/icon128.png`) included directly.
- **Service Worker (`background.js`)**:
  - Handles message type `translate`: calls `POST http://127.0.0.1:8000/analyze` and `POST http://127.0.0.1:8000/parse`. Returns lemma, part of speech, morphology, gloss, and syntax.
  - Handles message type `getGrammar`: calls `POST http://127.0.0.1:8000/parse` to extract subject, direct object, and ablative constructions.
  - Handles message types `loadHistory`, `loadVocabulary`, and `saveVocabularyItem`.
  - Enforces capacity limits: history (max 20 items), personal vocabulary (max 100 items).
  - If the FastAPI server is unreachable, displays a clear instructional error:
    `API server is not running. Please start it with: uvicorn latin_nlp.api:app --reload`
    (Never falls back to simulated strings).
- **Popup (`popup.html`, `popup.js`, `popup.css`)**:
  - Interactive Latin input with instant morphology table and syntax breakdown.
  - One-click `+` button to save lemmas directly into the personal vocabulary list.
  - History list with click-to-replay functionality.
- **Content Script (`content.js`)**:
  - Listens for text selections on any webpage.
  - Calls `getGrammar` and displays a floating, dismissible overlay with syntactic analysis (subject, object, ablatives, indirect statements).

## How to Install and Run

1. **Start the FastAPI backend server**:
   ```bash
   uvicorn latin_nlp.api:app --reload
   ```
2. **Load the extension in Chrome**:
   - Open `chrome://extensions` in Google Chrome.
   - Enable **Developer mode** (toggle in top right).
   - Click **Load unpacked**.
   - Select the `extension/` directory.
