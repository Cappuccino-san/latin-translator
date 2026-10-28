// background.js - Latin Translator Manifest V3 service worker

const API_BASE = "http://127.0.0.1:8000";
const HISTORY_KEY = "latinTranslatorHistory";
const VOCABULARY_KEY = "latinTranslatorVocabulary";

const SERVER_DOWN_MSG = "API server is not running. Please start it with:\nuvicorn latin_nlp.api:app --reload";

// Message Router
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "translate") {
    handleTranslateRequest(request.text, sendResponse);
    return true; // asynchronous response
  } else if (request.type === "getGrammar") {
    handleGetGrammarRequest(request.text, sendResponse);
    return true;
  } else if (request.type === "loadHistory") {
    loadFromStorage(HISTORY_KEY, sendResponse);
    return true;
  } else if (request.type === "loadVocabulary") {
    loadFromStorage(VOCABULARY_KEY, sendResponse);
    return true;
  } else if (request.type === "saveVocabularyItem") {
    addToVocabularyList(request.item, sendResponse);
    return true;
  }
});

// Translation & Morphological Analysis Handler
async function handleTranslateRequest(latinText, sendResponse) {
  try {
    const [analyzeRes, parseRes] = await Promise.all([
      fetch(`${API_BASE}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: latinText, top_n: 3 }),
      }),
      fetch(`${API_BASE}/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: latinText }),
      }),
    ]);

    if (!analyzeRes.ok || !parseRes.ok) {
      throw new Error(`API responded with status: ${analyzeRes.status} / ${parseRes.status}`);
    }

    const analyzeData = await analyzeRes.json();
    const parseData = await parseRes.json();

    // Build human-readable word glosses & primary translation
    const glosses = [];
    const tokens = [];

    for (const t of analyzeData.tokens || []) {
      const best = t.analyses && t.analyses.length > 0 ? t.analyses[0] : null;
      if (best && !best.unknown) {
        glosses.push(best.gloss || best.lemma);
        const morphFeatures = [
          best.case,
          best.number,
          best.gender,
          best.person ? `${best.person}p` : null,
          best.tense,
          best.mood,
          best.voice,
        ]
          .filter(Boolean)
          .join(" ");

        tokens.push({
          word: t.original,
          lemma: best.lemma,
          pos: best.pos,
          morphology: morphFeatures || "indeclinable",
          gloss: best.gloss,
          confidence: best.confidence,
          allAnalyses: t.analyses,
        });
      } else {
        tokens.push({
          word: t.original,
          lemma: t.original,
          pos: "unknown",
          morphology: "unrecognized",
          gloss: "unknown",
          confidence: 0.0,
          allAnalyses: [],
        });
      }
    }

    const mainTranslation = glosses.length > 0 ? glosses.join(" ") : "(No glosses available)";

    await saveToHistory(latinText, mainTranslation);

    sendResponse({
      success: true,
      text: latinText,
      translation: mainTranslation,
      tokens: tokens,
      parse: parseData,
      coverage: analyzeData.coverage,
      knownTokens: analyzeData.known_tokens,
      totalTokens: analyzeData.known_tokens + analyzeData.unknown_tokens,
    });
  } catch (error) {
    console.error("Translation request failed:", error);
    sendResponse({
      success: false,
      serverDown: true,
      error: SERVER_DOWN_MSG,
    });
  }
}

// Grammatical Parsing Request Handler for Selection Overlay
async function handleGetGrammarRequest(latinText, sendResponse) {
  try {
    const parseRes = await fetch(`${API_BASE}/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: latinText }),
    });

    if (!parseRes.ok) {
      throw new Error(`Parse API error: ${parseRes.status}`);
    }

    const parseData = await parseRes.json();

    // Format human-readable grammatical breakdown
    const lines = [];

    if (parseData.verb) {
      const v = parseData.verb;
      const vMorph = [v.person ? `${v.person}p` : null, v.number, v.tense, v.mood, v.voice]
        .filter(Boolean)
        .join(" ");
      lines.push(`Verb: ${v.form} (${v.lemma}) [${vMorph}] - "${v.gloss}"`);
    } else {
      lines.push("Verb: none identified");
    }

    if (parseData.subject && parseData.subject.length > 0) {
      lines.push(`Subject: ${parseData.subject.join(", ")}`);
    } else {
      lines.push("Subject: not explicitly found");
    }

    if (parseData.direct_object && parseData.direct_object.length > 0) {
      lines.push(`Direct Object: ${parseData.direct_object.join(", ")}`);
    }

    if (parseData.ablatives && parseData.ablatives.length > 0) {
      for (const ab of parseData.ablatives) {
        lines.push(`Ablative (${ab.kind}): ${ab.tokens.join(" ")}`);
      }
    }

    if (parseData.indirect_statements && parseData.indirect_statements.length > 0) {
      for (const ind of parseData.indirect_statements) {
        lines.push(`Indirect Statement: [${ind.subject_accusative}] + [${ind.infinitive}]`);
      }
    }

    const grammarSummary = lines.join("\n");

    sendResponse({
      success: true,
      grammar: grammarSummary,
      raw: parseData,
    });
  } catch (error) {
    console.error("Grammar request failed:", error);
    sendResponse({
      success: false,
      serverDown: true,
      grammar: SERVER_DOWN_MSG,
    });
  }
}

// History Management (Max 20)
async function saveToHistory(originalText, translatedText) {
  try {
    const result = await chrome.storage.sync.get([HISTORY_KEY]);
    let history = result[HISTORY_KEY] || [];
    history.unshift({
      original: originalText,
      translation: translatedText,
      timestamp: new Date().toISOString(),
    });
    if (history.length > 20) {
      history = history.slice(0, 20);
    }
    await chrome.storage.sync.set({ [HISTORY_KEY]: history });
  } catch (error) {
    console.error("Error saving history:", error);
  }
}

// Vocabulary Management (Max 100)
async function addToVocabularyList(item, sendResponse) {
  try {
    const result = await chrome.storage.sync.get([VOCABULARY_KEY]);
    let vocabulary = result[VOCABULARY_KEY] || [];
    const exists = vocabulary.some((v) => v.word.toLowerCase() === item.word.toLowerCase());
    if (!exists) {
      vocabulary.unshift(item);
      if (vocabulary.length > 100) {
        vocabulary = vocabulary.slice(0, 100);
      }
      await chrome.storage.sync.set({ [VOCABULARY_KEY]: vocabulary });
      if (sendResponse) sendResponse({ success: true, vocabulary: vocabulary });
    } else {
      if (sendResponse) sendResponse({ success: false, message: "Item already exists", vocabulary: vocabulary });
    }
  } catch (error) {
    console.error("Error saving vocabulary:", error);
    if (sendResponse) sendResponse({ success: false, error: error.message });
  }
}

// Generic Storage Loader
async function loadFromStorage(key, sendResponse) {
  try {
    const result = await chrome.storage.sync.get([key]);
    sendResponse({ data: result[key] || [] });
  } catch (error) {
    console.error(`Error loading ${key}:`, error);
    sendResponse({ error: error.message, data: [] });
  }
}
