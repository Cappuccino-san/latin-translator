document.addEventListener("DOMContentLoaded", function() {
  const latinInput = document.getElementById("latin-input");
  const translateButton = document.getElementById("translate-button");
  const resultsDiv = document.getElementById("results");
  const historyListUL = document.getElementById("history-list"); // Renamed for clarity
  const vocabularyListUL = document.getElementById("vocabulary-list"); // Renamed for clarity

  // Load history and vocabulary from storage when popup opens
  loadHistory();
  loadVocabulary();

  translateButton.addEventListener("click", function() {
    const inputText = latinInput.value.trim();
    if (inputText) {
      chrome.runtime.sendMessage({ type: "translate", text: inputText }, function(response) {
        if (chrome.runtime.lastError) {
          resultsDiv.innerHTML = `<p>Error: ${chrome.runtime.lastError.message}</p>`;
          console.error("Translation error:", chrome.runtime.lastError.message);
          return;
        }
        if (response && response.translation) {
          displayTranslation(inputText, response.translation, response.alternatives || []);
          // History is saved by background.js, so we just reload the UI here
          loadHistory(); 
        } else {
          resultsDiv.innerHTML = "<p>No translation received or an error occurred.</p>";
        }
      });
    }
  });

  function displayTranslation(originalText, mainTranslation, alternatives) {
    let html = `<p><strong>Original:</strong> ${originalText}</p>`;
    html += `<p><strong>Main Translation:</strong> ${mainTranslation}</p>`;
    
    // Add to vocabulary button (example)
    html += `<button class="add-to-vocab" data-latin="${originalText}" data-english="${mainTranslation}">Add to Vocabulary</button>`;

    if (alternatives.length > 0) {
      html += "<p><strong>Alternative Translations:</strong></p><ul>";
      alternatives.forEach(alt => {
        html += `<li>${alt}</li>`;
      });
      html += "</ul>";
    }
    resultsDiv.innerHTML = html;

    // Add event listener for the new "Add to Vocabulary" button
    const vocabButton = resultsDiv.querySelector(".add-to-vocab");
    if (vocabButton) {
        vocabButton.addEventListener("click", function() {
            const latinWord = this.dataset.latin;
            const englishWord = this.dataset.english;
            // For simplicity, we're adding the whole input as a "word". This could be refined.
            addToVocabulary(latinWord, englishWord);
        });
    }
  }

  function renderHistoryList(historyItems) {
    historyListUL.innerHTML = ""; // Clear existing list
    if (!historyItems || historyItems.length === 0) {
        historyListUL.innerHTML = "<li>No history yet.</li>";
        return;
    }
    historyItems.forEach(item => {
      const listItem = document.createElement("li");
      listItem.textContent = `"${item.original.substring(0, 20)}..." -> "${item.translation.substring(0, 20)}..."`;
      listItem.title = `Full: ${item.original} -> ${item.translation} (${new Date(item.timestamp).toLocaleString()})`;
      listItem.style.cursor = "pointer";
      listItem.addEventListener("click", () => {
        latinInput.value = item.original;
        // Re-request translation to show alternatives if any, or just display stored translation
        chrome.runtime.sendMessage({ type: "translate", text: item.original }, function(response) {
            if (response && response.translation) {
                displayTranslation(item.original, response.translation, response.alternatives || []);
            }
        });
      });
      historyListUL.appendChild(listItem);
    });
  }

  function loadHistory() {
    chrome.runtime.sendMessage({ type: "loadHistory" }, function(response) {
      if (chrome.runtime.lastError) {
        console.error("Error loading history:", chrome.runtime.lastError.message);
        historyListUL.innerHTML = "<li>Error loading history.</li>";
        return;
      }
      if (response && response.data) {
        renderHistoryList(response.data);
      } else {
        historyListUL.innerHTML = "<li>Could not load history.</li>";
      }
    });
  }

  function renderVocabularyList(vocabularyItems) {
    vocabularyListUL.innerHTML = ""; // Clear existing list
    if (!vocabularyItems || vocabularyItems.length === 0) {
        vocabularyListUL.innerHTML = "<li>Vocabulary is empty.</li>";
        return;
    }
    vocabularyItems.forEach(item => {
      const listItem = document.createElement("li");
      listItem.textContent = `${item.word}: ${item.definition}`;
      // Add functionality to remove from vocab or view details if needed
      vocabularyListUL.appendChild(listItem);
    });
  }

  function loadVocabulary() {
    chrome.runtime.sendMessage({ type: "loadVocabulary" }, function(response) {
      if (chrome.runtime.lastError) {
        console.error("Error loading vocabulary:", chrome.runtime.lastError.message);
        vocabularyListUL.innerHTML = "<li>Error loading vocabulary.</li>";
        return;
      }
      if (response && response.data) {
        renderVocabularyList(response.data);
      } else {
        vocabularyListUL.innerHTML = "<li>Could not load vocabulary.</li>";
      }
    });
  }

  function addToVocabulary(latinWord, englishDefinition) {
    chrome.runtime.sendMessage({ type: "saveVocabularyItem", item: { word: latinWord, definition: englishDefinition } }, function(response) {
        if (chrome.runtime.lastError) {
            console.error("Error saving vocab:", chrome.runtime.lastError.message);
            // Optionally notify user in UI
            return;
        }
        if (response && response.success) {
            console.log("Vocabulary item saved successfully.");
            loadVocabulary(); // Refresh the list
        } else {
            console.log("Failed to save vocabulary item:", response ? response.message : "Unknown error");
            // Optionally notify user in UI if item already exists or other error
        }
    });
  }
});

