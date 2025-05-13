import { useState, useEffect, useCallback, CSSProperties } from 'react';

// Define interfaces for our state objects
interface HistoryEntry {
  latin: string;
  english: string;
  timestamp: string;
}

interface VocabularyEntry {
  latin: string;
  english: string;
}

// Helper functions for local storage
const getFromLocalStorage = <T,>(key: string, defaultValue: T): T => {
  if (typeof window !== 'undefined') {
    const storedValue = localStorage.getItem(key);
    if (storedValue) {
      try {
        return JSON.parse(storedValue) as T;
      } catch (error) {
        console.error(`Error parsing localStorage key "${key}":`, error);
        return defaultValue;
      }
    }
  }
  return defaultValue;
};

const saveToLocalStorage = <T,>(key: string, value: T) => {
  if (typeof window !== 'undefined') {
    localStorage.setItem(key, JSON.stringify(value));
  }
};

// --- Simulated Translation and Grammar Engine ---
const fetchSimulatedTranslationAndGrammar = async (latinText: string): Promise<{ translation: string; grammar: string[] }> => {
  console.log(`Simulated engine: Processing "${latinText}"`);
  await new Promise(resolve => setTimeout(resolve, 300)); // Simulate network delay

  let translation = `(Simulated) English for: ${latinText}`;
  let grammar: string[] = [];
  const words = latinText.toLowerCase().split(/\s+/).filter(w => w.length > 0);

  if (words.includes("amo")) {
    translation = "I love (Simulated)";
    grammar.push("amo: Verb, 1st person singular, present active indicative of amare (to love) (Simulated)");
  } else if (words.includes("regina")) {
    translation = "Queen (Simulated)";
    grammar.push("regina: Noun, feminine, singular, nominative/vocative/ablative (queen) (Simulated)");
  } else if (words.includes("aqua")) {
    translation = "Water (Simulated)";
    grammar.push("aqua: Noun, feminine, singular, nominative/vocative (water) (Simulated)");
  }

  if (grammar.length === 0 && words.length > 0) {
    grammar.push(`${words[0]}: (Simulated) Grammatical information for the first word.`);
    if (words.length > 1) {
      grammar.push(`${words[1]}: (Simulated) Grammatical information for the second word.`);
    }
  }
  if (grammar.length === 0 && words.length === 0 && latinText.length > 0) {
    grammar.push("No specific simulated grammar rules matched for the input.")
  } else if (grammar.length === 0 && latinText.length > 0) {
    grammar.push("No specific simulated grammar rules matched.")
  }
  return { translation, grammar };
};
// --- End Simulated Engine ---

export default function LatinTranslatorPage() {
  const [latinInput, setLatinInput] = useState<string>('');
  const [translationOutput, setTranslationOutput] = useState<string>('');
  const [grammarInfo, setGrammarInfo] = useState<string[]>([]);
  const [showGrammar, setShowGrammar] = useState<boolean>(false);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [vocabulary, setVocabulary] = useState<VocabularyEntry[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  useEffect(() => {
    setHistory(getFromLocalStorage<HistoryEntry[]>('latinWebHistory', []));
    setVocabulary(getFromLocalStorage<VocabularyEntry[]>('latinWebVocabulary', []));
  }, []);

  useEffect(() => {
    saveToLocalStorage<HistoryEntry[]>('latinWebHistory', history);
  }, [history]);

  useEffect(() => {
    saveToLocalStorage<VocabularyEntry[]>('latinWebVocabulary', vocabulary);
  }, [vocabulary]);

  const handleTranslate = useCallback(async () => {
    if (!latinInput.trim()) return;
    setIsLoading(true);
    setShowGrammar(false);

    try {
      const { translation, grammar } = await fetchSimulatedTranslationAndGrammar(latinInput);
      setTranslationOutput(translation);
      setGrammarInfo(grammar);

      const newHistoryEntry: HistoryEntry = { latin: latinInput, english: translation, timestamp: new Date().toISOString() };
      setHistory(prevHistory => [newHistoryEntry, ...prevHistory.slice(0, 19)]);
    } catch (error) {
      console.error("Error during translation:", error);
      setTranslationOutput("Error fetching translation.");
      setGrammarInfo([]);
    }
    setIsLoading(false);
  }, [latinInput]);

  const handleAddToVocabulary = useCallback(() => {
    if (!latinInput.trim() || !translationOutput.trim() || translationOutput.startsWith("Error")) return;
    const newVocabEntry: VocabularyEntry = { latin: latinInput, english: translationOutput };
    if (!vocabulary.find(item => item.latin.toLowerCase() === newVocabEntry.latin.toLowerCase())) {
      setVocabulary(prevVocab => [newVocabEntry, ...prevVocab.slice(0, 49)]);
    }
  }, [latinInput, translationOutput, vocabulary]);
  
  const handleHistoryClick = useCallback(async (entry: HistoryEntry) => {
    setLatinInput(entry.latin);
    setIsLoading(true);
    try {
        const { translation, grammar } = await fetchSimulatedTranslationAndGrammar(entry.latin);
        setTranslationOutput(translation);
        setGrammarInfo(grammar);
    } catch (error) {
        console.error("Error re-translating from history:", error);
        setTranslationOutput("Error fetching translation from history.");
        setGrammarInfo([]);
    }
    setShowGrammar(false);
    setIsLoading(false);
  }, []);

  const styles: { [key: string]: CSSProperties } = {
    container: { padding: '20px', fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif', maxWidth: '800px', margin: '0 auto', color: '#333' },
    header: { textAlign: 'center' as CSSProperties['textAlign'], marginBottom: '40px', color: '#2c3e50' },
    h1: { fontSize: '2.5em', marginBlockEnd: '0.2em'},
    section: { marginBottom: '30px' },
    h2: { fontSize: '1.5em', color: '#34495e', borderBottom: '2px solid #ecf0f1', paddingBottom: '10px', marginBottom: '20px'},
    textarea: { width: '100%', padding: '12px', border: '1px solid #bdc3c7', borderRadius: '4px', boxSizing: 'border-box', fontSize: '1em', minHeight: '100px' },
    button: { marginTop: '15px', padding: '12px 25px', backgroundColor: '#3498db', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '1em', transition: 'background-color 0.2s ease' },
    buttonSecondary: { backgroundColor: '#95a5a6', marginLeft: '10px' },
    buttonDisabled: { opacity: 0.6, cursor: 'not-allowed' },
    outputSection: { padding: '20px', border: '1px solid #ecf0f1', borderRadius: '4px', backgroundColor: '#f8f9f9', marginTop: '20px' },
    outputParagraph: { fontSize: '1.1em', margin: '0 0 15px 0', lineHeight: '1.6' },
    listContainer: { display: 'flex', flexDirection: 'row' as CSSProperties['flexDirection'], justifyContent: 'space-between', gap: '30px' }, // md: { flexDirection: 'row' } removed as it's not standard CSSProperties
    listSection: { flex: 1, minWidth: '0' },
    list: { listStyleType: 'none', padding: '0', maxHeight: '250px', overflowY: 'auto' as CSSProperties['overflowY'], border: '1px solid #ecf0f1', borderRadius: '4px', backgroundColor: 'white' },
    listItem: { padding: '10px 12px', borderBottom: '1px solid #f0f0f0', cursor: 'pointer', transition: 'background-color 0.2s ease' },
    listItemHover: { backgroundColor: '#e8f4fd' }, 
    footer: { textAlign: 'center' as CSSProperties['textAlign'], marginTop: '50px', paddingTop: '20px', borderTop: '1px solid #ecf0f1', fontSize: '0.9em', color: '#7f8c8d' }
  };

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.h1}>Latin to English Translator</h1>
      </header>

      <main>
        <section style={styles.section}>
          <h2 style={styles.h2}>Enter Latin Text</h2>
          <textarea
            value={latinInput}
            onChange={(e) => setLatinInput(e.target.value)}
            placeholder="Type or paste Latin text here..."
            rows={5}
            style={styles.textarea}
          />
          <button
            onClick={handleTranslate}
            style={{...styles.button, ...(isLoading ? styles.buttonDisabled : {})}}
            disabled={isLoading}
          >
            {isLoading ? 'Translating...' : 'Translate'}
          </button>
        </section>

        {translationOutput && (
          <section style={{...styles.outputSection, marginBottom: '20px'}}>
            <h2 style={styles.h2}>Translation</h2>
            <p style={styles.outputParagraph}>{translationOutput}</p>
            <button 
              onClick={handleAddToVocabulary}
              style={{...styles.button, ...styles.buttonSecondary, padding: '8px 15px', fontSize: '0.9em', ...(isLoading || !translationOutput || translationOutput.startsWith("Error") ? styles.buttonDisabled : {})}}
              disabled={isLoading || !translationOutput || translationOutput.startsWith("Error")}>
                Add to Vocabulary
            </button>
            <button 
              onClick={() => setShowGrammar(!showGrammar)}
              style={{...styles.button, ...styles.buttonSecondary, padding: '8px 15px', fontSize: '0.9em', ...(isLoading || grammarInfo.length === 0 ? styles.buttonDisabled : {})}}
              disabled={isLoading || grammarInfo.length === 0}>
              {showGrammar ? 'Hide' : 'Show'} Grammatical Info
            </button>
          </section>
        )}

        {showGrammar && grammarInfo.length > 0 && (
          <section style={{...styles.outputSection, backgroundColor: '#eaf5ff', marginBottom: '20px'}}>
            <h2 style={styles.h2}>Grammatical Information</h2>
            <ul style={{ listStyleType: 'disc', paddingLeft: '20px', margin: '0' }}>
              {grammarInfo.map((info, index) => (
                <li key={index} style={{ marginBottom: '8px', lineHeight: '1.5' }}>{info}</li>
              ))}
            </ul>
          </section>
        )}

        <div style={styles.listContainer}>
          <section style={{...styles.section, ...styles.listSection}}>
            <h2 style={styles.h2}>History</h2>
            {history.length === 0 ? <p>No history yet.</p> :
              <ul style={styles.list}>
                {history.map((entry, index) => (
                  <li 
                    key={index} 
                    onClick={() => handleHistoryClick(entry)} 
                    style={styles.listItem}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = styles.listItemHover.backgroundColor!}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = index % 2 === 0 ? '#f9f9f9' : 'white'}
                  >
                    {`${entry.latin.substring(0, 30)}${entry.latin.length > 30 ? '...' : ''}`}
                  </li>
                ))}
              </ul>
            }
          </section>

          <section style={{...styles.section, ...styles.listSection}}>
            <h2 style={styles.h2}>Vocabulary</h2>
            {vocabulary.length === 0 ? <p>Vocabulary is empty.</p> :
              <ul style={styles.list}>
                {vocabulary.map((item, index) => (
                  <li key={index} style={{...styles.listItem, cursor: 'default', backgroundColor: index % 2 === 0 ? '#f9f9f9' : 'white' }}>
                    <strong>{item.latin}:</strong> {item.english}
                  </li>
                ))}
              </ul>
            }
          </section>
        </div>
      </main>

      <footer style={styles.footer}>
        <p>Latin Translator Website - Created by Manus</p>
      </footer>
    </div>
  );
}

