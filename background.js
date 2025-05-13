// background.js

// --- Storage Keys ---
const HISTORY_KEY = "latinTranslatorHistory";
const VOCABULARY_KEY = "latinTranslatorVocabulary";

let alpheiosEmbeddedUtil = null;

// --- Alpheios Initialization (Attempt) ---
async function initializeAlpheios() {
  if (alpheiosEmbeddedUtil) return alpheiosEmbeddedUtil;

  try {
    // Dynamically import the Alpheios embedded library from CDN
    // This is an attempt; actual usage in a service worker might need adjustments
    // or local bundling of the library if possible and permitted.
    const AlpheiosEmbed = await import("https://cdn.jsdelivr.net/npm/alpheios-embedded@latest/dist/alpheios-embedded.min.js");
    
    // The Alpheios library might need to import its own dependencies.
    // The original example was: window.AlpheiosEmbed.importDependencies({ mode: 'cdn' })
    // We need to see if this can be adapted for a service worker context.
    // For now, we assume the main module import is enough or it handles its deps.

    // The Alpheios Embedded library is primarily for UI enhancement.
    // We need to find out if it exposes programmatic APIs for morphology and lexicon lookups.
    // This is a placeholder for how one might get a utility object.
    // The actual API might be different.
    // const AlpheiosModules = await AlpheiosEmbed.default.importDependencies({ mode: 'cdn' });
    // alpheiosEmbeddedUtil = new AlpheiosModules.Models.LexiconFull("lat"); // Example, API needs verification

    // For now, we will simulate that initialization provides some utility.
    // This part is highly dependent on Alpheios actual programmatic API for headless use.
    // If Alpheios is purely UI-driven, another solution (e.g., Whitaker's Words JS port) would be needed.
    console.log("Alpheios Embedded library loaded (simulated successful import).");
    alpheiosEmbeddedUtil = {
      // Placeholder for actual Alpheios API calls
      getMorphology: async (text, lang = "lat") => {
        console.log(`Alpheios (simulated): Getting morphology for '${text}'`);
        // This would interact with Alpheios's morphological analyzer
        if (text.toLowerCase() === "amo") {
          return [{ part: "verb", tense: "pres", voice: "act", mood: "ind", person: "1st", number: "sg", lemma: "amare" }];
        }
        if (text.toLowerCase() === "regina") {
            return [{ part: "noun", gender: "fem", number: "sg", case: "nom", lemma: "regina" }];
        }
        return [{ error: "Morphology not found (simulated)" }];
      },
      getShortDefs: async (text, lang = "lat") => {
        console.log(`Alpheios (simulated): Getting definitions for '${text}'`);
        // This would interact with Alpheios's lexicon
        if (text.toLowerCase().includes("amo")) {
          return [{ shortdef: "to love, like" }];
        }
        if (text.toLowerCase().includes("aqua")) {
            return [{ shortdef: "water" }];
        }
        return [{ error: "Definition not found (simulated)" }];
      }
    };
    return alpheiosEmbeddedUtil;

  } catch (error) {
    console.error("Failed to initialize Alpheios:", error);
    alpheiosEmbeddedUtil = null; // Ensure it's null on failure
    return null;
  }
}

// Call initialization early
initializeAlpheios().then(util => {
  if (util) {
    console.log("Alpheios (simulated) initialized successfully.");
  } else {
    console.warn("Alpheios (simulated) initialization failed. Using fallback mocks.");
  }
});

// --- Event Listeners ---
chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
  if (request.type === "translate") {
    handleTranslateRequest(request.text, sendResponse);
    return true; // Indicates that the response will be sent asynchronously
  } else if (request.type === "getGrammar") {
    handleGetGrammarRequest(request.text, sendResponse);
    return true; // Indicates that the response will be sent asynchronously
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

// --- Translation Request Handler ---
async function handleTranslateRequest(latinText, sendResponse) {
  console.log("Background: Received translation request for:", latinText);
  const alpheios = await initializeAlpheios(); // Ensure initialized
  let mainTranslation = "(Fallback) English translation for " + latinText;
  let alternatives = [];

  if (alpheios && alpheios.getShortDefs) {
    try {
      const defs = await alpheios.getShortDefs(latinText);
      if (defs && defs.length > 0 && !defs[0].error) {
        mainTranslation = defs.map(d => d.shortdef).join('; ');
        // Alternatives could come from multiple senses or related words if API supports
      } else {
        mainTranslation = defs[0] ? defs[0].error : "No definition found (Alpheios simulated).";
      }
    } catch (e) {
      console.error("Alpheios getShortDefs error:", e);
      mainTranslation = "Error during Alpheios translation (simulated).";
    }
  } else {
    // Fallback to simpler mock if Alpheios failed to init
    if (latinText.toLowerCase().includes("amo")) {
        mainTranslation = "I love (Fallback Mock)";
        alternatives = ["I like (Fallback Mock)", "I am fond of (Fallback Mock)"];
    } else if (latinText.toLowerCase().includes("aqua")) {
        mainTranslation = "Water (Fallback Mock)";
    }
  }
  
  saveToHistory(latinText, mainTranslation);
  sendResponse({
      translation: mainTranslation,
      alternatives: alternatives
  });
}

// --- Grammatical Analysis Request Handler ---
async function handleGetGrammarRequest(latinWord, sendResponse) {
  console.log("Background: Received grammar request for:", latinWord);
  const alpheios = await initializeAlpheios(); // Ensure initialized
  let grammarResult = "(Fallback) Grammatical information for " + latinWord;

  if (alpheios && alpheios.getMorphology) {
    try {
      const morphInfos = await alpheios.getMorphology(latinWord);
      if (morphInfos && morphInfos.length > 0 && !morphInfos[0].error) {
        // Format morphology info (this is a simple example)
        grammarResult = morphInfos.map(info => 
            `Lemma: ${info.lemma || 'N/A'}, Part: ${info.part || 'N/A'}, Features: ${Object.entries(info).filter(([key]) => !['lemma', 'part'].includes(key)).map(([key, value]) => `${key}: ${value}`).join(', ')}`
        ).join('\n---\n');
      } else {
        grammarResult = morphInfos[0] ? morphInfos[0].error : "No morphology found (Alpheios simulated).";
      }
    } catch (e) {
      console.error("Alpheios getMorphology error:", e);
      grammarResult = "Error during Alpheios grammar analysis (simulated).";
    }
  } else {
    // Fallback to simpler mock if Alpheios failed to init
    if (latinWord.toLowerCase() === "amo") {
        grammarResult = "Verb, 1st person singular, present active indicative of amare (to love). (Fallback Mock)";
    } else if (latinWord.toLowerCase() === "regina") {
        grammarResult = "Noun, feminine, singular, nominative (queen). (Fallback Mock)";
    }
  }
  sendResponse({ grammar: grammarResult });
}

// --- History Management ---
async function saveToHistory(originalText, translatedText) {
  try {
    const result = await chrome.storage.sync.get([HISTORY_KEY]);
    let history = result[HISTORY_KEY] || [];
    history.unshift({ original: originalText, translation: translatedText, timestamp: new Date().toISOString() });
    if (history.length > 20) { // Keep last 20 history items
      history = history.slice(0, 20);
    }
    await chrome.storage.sync.set({ [HISTORY_KEY]: history });
    console.log("History saved");
  } catch (error) {
    console.error("Error saving history:", error);
  }
}

// --- Vocabulary Management ---
async function addToVocabularyList(item, sendResponse) {
  try {
    const result = await chrome.storage.sync.get([VOCABULARY_KEY]);
    let vocabulary = result[VOCABULARY_KEY] || [];
    const exists = vocabulary.some(v => v.word.toLowerCase() === item.word.toLowerCase());
    if (!exists) {
        vocabulary.unshift(item); 
        if (vocabulary.length > 100) { 
            vocabulary = vocabulary.slice(0,100);
        }
        await chrome.storage.sync.set({ [VOCABULARY_KEY]: vocabulary });
        console.log("Vocabulary item saved:", item);
        if (sendResponse) sendResponse({success: true, vocabulary: vocabulary});
    } else {
        console.log("Vocabulary item already exists:", item);
        if (sendResponse) sendResponse({success: false, message: "Item already exists", vocabulary: vocabulary});
    }

  } catch (error) {
    console.error("Error saving vocabulary item:", error);
    if (sendResponse) sendResponse({success: false, error: error.message});
  }
}

// --- Generic Storage Loader ---
async function loadFromStorage(key, sendResponse) {
  try {
    const result = await chrome.storage.sync.get([key]);
    sendResponse({ data: result[key] || [] });
  } catch (error) {
    console.error(`Error loading ${key} from storage:`, error);
    sendResponse({ error: error.message, data: [] });
  }
}

console.log("Background service worker started. Attempting Alpheios initialization.");

