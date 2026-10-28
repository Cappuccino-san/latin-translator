// popup.js - UI controller for Latin Translator extension

document.addEventListener("DOMContentLoaded", () => {
  const latinInput = document.getElementById("latin-input");
  const translateButton = document.getElementById("translate-button");
  const resultsDiv = document.getElementById("results");
  const historyListUL = document.getElementById("history-list");
  const vocabularyListUL = document.getElementById("vocabulary-list");

  // Load history & vocabulary on open
  loadHistory();
  loadVocabulary();

  translateButton.addEventListener("click", () => {
    const text = latinInput.value.trim();
    if (!text) return;

    resultsDiv.innerHTML = "<p><em>Analyzing Latin text...</em></p>";

    chrome.runtime.sendMessage({ type: "translate", text }, (response) => {
      if (chrome.runtime.lastError) {
        renderError(chrome.runtime.lastError.message);
        return;
      }
      if (!response || !response.success) {
        renderError(response?.error || "Unknown error occurred.");
        return;
      }
      renderTranslationResults(response);
      loadHistory();
    });
  });

  function renderError(message) {
    resultsDiv.innerHTML = `
      <div class="error-box">
        <p><strong>⚠️ Connection Error</strong></p>
        <p>${message.replace(/\n/g, "<br>")}</p>
      </div>`;
  }

  function renderTranslationResults(res) {
    let html = `<div class="translation-summary">
      <p><strong>Coverage:</strong> ${res.knownTokens}/${res.totalTokens} tokens (${Math.round(res.coverage * 100)}%)</p>
      <p><strong>Glosses:</strong> ${escapeHtml(res.translation)}</p>
    </div>`;

    // Word-by-word Analysis Table
    if (res.tokens && res.tokens.length > 0) {
      html += `<h3>Words & Morphology</h3>
      <table class="analysis-table">
        <thead>
          <tr>
            <th>Word</th>
            <th>Lemma</th>
            <th>POS</th>
            <th>Morphology</th>
            <th>Gloss</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>`;

      res.tokens.forEach((t) => {
        html += `
          <tr>
            <td><strong>${escapeHtml(t.word)}</strong></td>
            <td><em>${escapeHtml(t.lemma)}</em></td>
            <td>${escapeHtml(t.pos)}</td>
            <td>${escapeHtml(t.morphology)}</td>
            <td>${escapeHtml(t.gloss)}</td>
            <td>
              <button class="add-vocab-btn" data-word="${escapeHtml(t.lemma)}" data-gloss="${escapeHtml(t.gloss)}" data-pos="${escapeHtml(t.pos)}">+</button>
            </td>
          </tr>`;
      });
      html += `</tbody></table>`;
    }

    // Syntax Parse Section
    if (res.parse) {
      const p = res.parse;
      html += `<h3>Syntax Parse</h3><div class="syntax-box">`;

      if (p.verb) {
        html += `<p><strong>Verb:</strong> ${escapeHtml(p.verb.form)} (lemma: <em>${escapeHtml(p.verb.lemma)}</em>)</p>`;
      }
      if (p.subject && p.subject.length > 0) {
        html += `<p><strong>Subject:</strong> ${escapeHtml(p.subject.join(", "))} <small>(${escapeHtml(p.subject_explanation)})</small></p>`;
      }
      if (p.direct_object && p.direct_object.length > 0) {
        html += `<p><strong>Direct Object:</strong> ${escapeHtml(p.direct_object.join(", "))} <small>(${escapeHtml(p.object_explanation)})</small></p>`;
      }
      if (p.ablatives && p.ablatives.length > 0) {
        html += `<p><strong>Ablative Constructions:</strong></p><ul>`;
        p.ablatives.forEach((ab) => {
          html += `<li>[${escapeHtml(ab.kind)}] <em>${escapeHtml(ab.tokens.join(" "))}</em> &mdash; ${escapeHtml(ab.explanation)}</li>`;
        });
        html += `</ul>`;
      }
      if (p.indirect_statements && p.indirect_statements.length > 0) {
        html += `<p><strong>Indirect Statements:</strong></p><ul>`;
        p.indirect_statements.forEach((ind) => {
          html += `<li>Accusative Subject: <strong>${escapeHtml(ind.subject_accusative)}</strong> + Infinitive: <strong>${escapeHtml(ind.infinitive)}</strong></li>`;
        });
        html += `</ul>`;
      }
      html += `</div>`;
    }

    resultsDiv.innerHTML = html;

    // Attach event listeners to vocabulary buttons
    resultsDiv.querySelectorAll(".add-vocab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const word = btn.dataset.word;
        const definition = `${btn.dataset.gloss} (${btn.dataset.pos})`;
        addToVocabulary(word, definition);
      });
    });
  }

  function loadHistory() {
    chrome.runtime.sendMessage({ type: "loadHistory" }, (response) => {
      if (chrome.runtime.lastError || !response || !response.data) {
        historyListUL.innerHTML = "<li>No history yet.</li>";
        return;
      }
      const history = response.data;
      if (history.length === 0) {
        historyListUL.innerHTML = "<li>No history yet.</li>";
        return;
      }
      historyListUL.innerHTML = "";
      history.slice(0, 20).forEach((item) => {
        const li = document.createElement("li");
        li.textContent = `${item.original} → ${item.translation}`;
        li.style.cursor = "pointer";
        li.title = "Click to reload text";
        li.addEventListener("click", () => {
          latinInput.value = item.original;
          translateButton.click();
        });
        historyListUL.appendChild(li);
      });
    });
  }

  function loadVocabulary() {
    chrome.runtime.sendMessage({ type: "loadVocabulary" }, (response) => {
      if (chrome.runtime.lastError || !response || !response.data) {
        vocabularyListUL.innerHTML = "<li>Vocabulary empty.</li>";
        return;
      }
      const vocab = response.data;
      if (vocab.length === 0) {
        vocabularyListUL.innerHTML = "<li>Vocabulary empty.</li>";
        return;
      }
      vocabularyListUL.innerHTML = "";
      vocab.slice(0, 100).forEach((item) => {
        const li = document.createElement("li");
        li.innerHTML = `<strong>${escapeHtml(item.word)}</strong>: ${escapeHtml(item.definition)}`;
        vocabularyListUL.appendChild(li);
      });
    });
  }

  function addToVocabulary(word, definition) {
    chrome.runtime.sendMessage(
      { type: "saveVocabularyItem", item: { word, definition } },
      (response) => {
        if (response && response.success) {
          loadVocabulary();
        } else if (response && response.message) {
          alert(response.message);
        }
      }
    );
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
