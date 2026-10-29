# Complete Virgil Corpus & Benchmark

## 1. Editions and Source Credit

All Latin text in the Virgil corpus is sourced from the authoritative **Perseus Digital Library** (Tufts University), using the edition edited by **J. B. Greenough (1900)**:

> *The Bucolics, Aeneid, and Georgics of Virgil*, edited by J. B. Greenough. Boston: Ginn and Company, 1900.

- **Author**: Publius Vergilius Maro (70 BCE – 19 BCE). The Latin text is in the public domain.
- **Digital Edition**: EpiDoc / TEI XML curated by the Perseus Project, licensed under [CC BY-SA 3.0 US](https://creativecommons.org/licenses/by-sa/3.0/us/).
- **Consistency**: All three works (*Aeneid*, *Eclogues*, and *Georgics*) use this exact same edition. No editions are mixed silently.

---

## 2. Corpus Structure (`data/virgil/`)

The full corpus is split systematically by work, book, and line:

```
data/virgil/
├── aeneid/
│   ├── book1.txt    (756 lines)
│   ├── book2.txt    (804 lines)
│   ├── book3.txt    (718 lines)
│   ├── book4.txt    (705 lines)
│   ├── book5.txt    (871 lines)
│   ├── book6.txt    (901 lines)
│   ├── book7.txt    (817 lines)
│   ├── book8.txt    (731 lines)
│   ├── book9.txt    (818 lines)
│   ├── book10.txt   (909 lines)
│   ├── book11.txt   (915 lines)
│   └── book12.txt   (952 lines)
├── eclogues/
│   ├── book1.txt    (84 lines)
│   ├── book2.txt    (73 lines)
│   ├── book3.txt    (111 lines)
│   ├── book4.txt    (63 lines)
│   ├── book5.txt    (90 lines)
│   ├── book6.txt    (86 lines)
│   ├── book7.txt    (70 lines)
│   ├── book8.txt    (109 lines)
│   ├── book9.txt    (67 lines)
│   └── book10.txt   (77 lines)
└── georgics/
    ├── book1.txt    (514 lines)
    ├── book2.txt    (542 lines)
    ├── book3.txt    (566 lines)
    └── book4.txt    (566 lines)
```

- **Aeneid**: 12 books, 9,897 verse lines, 63,795 word tokens.
- **Eclogues** (*Bucolica*): 10 poems, 830 verse lines, 5,632 word tokens.
- **Georgics**: 4 books, 2,188 verse lines, 14,185 word tokens.
- **Grand Total**: 26 files, 12,915 lines, 83,612 word tokens.

The curated test slices `data/aeneid/book1_1_11.txt` and `data/aeneid/book1_12_33.txt` remain untouched as permanent regression baselines.

---

## 3. Coverage Analysis (Per Work and Per Book)

Generated via `python eval/evaluate.py --virgil`:

### Aeneid (12 Books)
| Book | Lines | Known Tokens | Total Tokens | Coverage | Unknown Tokens |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 756 | 4,670 | 4,880 | **95.7%** | 210 |
| **2** | 804 | 4,888 | 5,216 | **93.7%** | 328 |
| **3** | 718 | 4,287 | 4,535 | **94.5%** | 248 |
| **4** | 705 | 4,319 | 4,574 | **94.4%** | 255 |
| **5** | 871 | 5,288 | 5,569 | **95.0%** | 281 |
| **6** | 901 | 5,495 | 5,861 | **93.8%** | 366 |
| **7** | 817 | 4,886 | 5,215 | **93.7%** | 329 |
| **8** | 731 | 4,332 | 4,628 | **93.6%** | 296 |
| **9** | 818 | 5,006 | 5,307 | **94.3%** | 301 |
| **10** | 909 | 5,597 | 5,899 | **94.9%** | 302 |
| **11** | 915 | 5,596 | 5,911 | **94.7%** | 315 |
| **12** | 952 | 5,900 | 6,200 | **95.2%** | 300 |
| **Total Aeneid** | **9,897** | **60,264** | **63,795** | **94.5%** | **3,531** |

### Eclogues (10 Poems)
| Poem | Lines | Known Tokens | Total Tokens | Coverage | Unknown Tokens |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 84 | 529 | 567 | **93.3%** | 38 |
| **2** | 73 | 461 | 492 | **93.7%** | 31 |
| **3** | 111 | 717 | 795 | **90.2%** | 78 |
| **4** | 63 | 377 | 409 | **92.2%** | 32 |
| **5** | 90 | 555 | 598 | **92.8%** | 43 |
| **6** | 86 | 502 | 558 | **90.0%** | 56 |
| **7** | 70 | 435 | 471 | **92.4%** | 36 |
| **8** | 109 | 702 | 750 | **93.6%** | 48 |
| **9** | 67 | 438 | 471 | **93.0%** | 33 |
| **10** | 77 | 483 | 521 | **92.7%** | 38 |
| **Total Eclogues** | **830** | **5,199** | **5,632** | **92.3%** | **433** |

### Georgics (4 Books)
| Book | Lines | Known Tokens | Total Tokens | Coverage | Unknown Tokens |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | 514 | 3,054 | 3,309 | **92.3%** | 255 |
| **2** | 542 | 3,255 | 3,520 | **92.5%** | 265 |
| **3** | 566 | 3,449 | 3,700 | **93.2%** | 251 |
| **4** | 566 | 3,396 | 3,656 | **92.9%** | 260 |
| **Total Georgics** | **2,188** | **13,154** | **14,185** | **92.7%** | **1,031** |

### Entire Virgil Corpus (Batch 44 Status)
- **Known Tokens**: 78,617 (up from 78,429 in Batch 43, 78,266 in Batch 42, 78,108 in Batch 41, 77,917 in Batch 40, 77,754 in Batch 39, and 25,585 baseline, +53,032 tokens recognized overall)
- **Unknown Tokens**: 4,995 (3,444 hapax legomena occurring exactly once, 1,551 non-hapax occurrences across 385 distinct forms)
- **Total Word Tokens**: 83,612
- **Overall Coverage**: **94.0%** (Aeneid 94.5%, Eclogues 92.3%, Georgics 92.7%)
- **Hapax vs Non-Hapax Split**:
  - Distinct unknown forms: 3,829
  - Hapax forms ($count = 1$): 3,444 forms (3,444 tokens, 69.0% of unknowns, 4.12% of corpus)
  - Non-hapax forms ($count \ge 2$): 385 forms (1,551 tokens, 31.0% of unknowns)
  - Theoretical non-hapax ceiling: **95.88%** ($(83,612 - 3,444) / 83,612 = 80,168 / 83,612$)

### Coverage Progression Across Frequency Batches
| Batch | Lexicon Size | Golden Forms | Virgil Known | Virgil Cov (%) | Token Delta | Remaining Unknowns |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Baseline** | 196 | 130 | 25,585 | 30.6% | — | 58,027 |
| **Batch 1–19** | 2,096 | 2,030 | 70,292 | 84.1% | +44,707 | 13,320 |
| **Batch 20** | 2,196 | 2,130 | 70,951 | 84.9% | +659 | 12,661 |
| **Batch 21** | 2,296 | 2,230 | 71,626 | 85.7% | +675 | 11,986 |
| **Batch 22** | 2,396 | 2,330 | 72,129 | 86.3% | +503 | 11,483 |
| **Batch 23** | 2,496 | 2,430 | 72,671 | 86.9% | +542 | 10,941 |
| **Batch 24** | 2,596 | 2,530 | 73,076 | 87.4% | +405 | 10,536 |
| **Batch 25** | 2,696 | 2,630 | 73,469 | 87.9% | +393 | 10,143 |
| **Batch 26** | 2,796 | 2,730 | 73,830 | 88.3% | +361 | 9,782 |
| **Batch 27** | 2,896 | 2,830 | 74,033 | 88.5% | +203 | 9,579 |
| **Batch 28** | 2,996 | 2,930 | 74,268 | 88.8% | +235 | 9,344 |
| **Batch 29** | 3,096 | 3,030 | 74,511 | 89.1% | +243 | 9,101 |
| **Batch 30** | 3,196 | 3,130 | 74,766 | 89.4% | +255 | 8,846 |
| **Batch 31** | 3,296 | 3,230 | 75,240 | 90.0% | +474 | 8,372 |
| **Batch 32** | 3,396 | 3,330 | 75,707 | 90.5% | +467 | 7,905 |
| **Batch 33** | 3,496 | 3,430 | 75,996 | 90.9% | +289 | 7,616 |
| **Batch 34** | 3,596 | 3,530 | 76,398 | 91.4% | +402 | 7,214 |
| **Batch 35** | 3,696 | 3,630 | 76,769 | 91.8% | +371 | 6,843 |
| **Batch 36** | 3,796 | 3,730 | 77,090 | 92.2% | +321 | 6,522 |
| **Batch 37** | 3,896 | 3,830 | 77,412 | 92.6% | +322 | 6,200 |
| **Batch 38** | 3,996 | 3,930 | 77,631 | 92.8% | +219 | 5,981 |
| **Batch 39** | 4,096 | 4,030 | 77,754 | 93.0% | +123 | 5,858 |
| **Batch 40** | 4,196 | 4,130 | 77,917 | 93.2% | +163 | 5,695 |
| **Batch 41** | 4,296 | 4,230 | 78,108 | 93.4% | +191 | 5,504 |
| **Batch 42** | 4,396 | 4,330 | 78,266 | 93.6% | +158 | 5,346 |
| **Batch 43** | 4,496 | 4,430 | 78,429 | 93.8% | +163 | 5,183 |
| **Batch 44** | 4,596 | 4,530 | 78,617 | 94.0% | +188 | 4,995 |

---

## 4. Caveat & Methodology

1. **In-Distribution Baseline**: Aeneid 1.1–33 exhibits **212 / 212 tokens known (100.0%)** because the curated lexicon was specifically expanded to cover the vocabulary of those introductory lines.
2. **Whole Corpus Honesty**: Across the entire 83,612-token body of Virgil's hexameter poetry, the 4,596 curated core stems recognize **94.0%** of all running tokens through regular Whitaker-style inflections and declensions. The remaining words are honestly reported as unknown with 0.0 confidence, never masked by hallucinated glosses or fallback translations.
3. **Token Coverage vs Parse Accuracy**: Note that coverage measures tokens recognized and inflected by the lexicon and morphology engine, not end-to-end full sentence dependency parse accuracy.


---

## 5. Public-Domain English Translations (`data/virgil/translation/`)

All translations provided in the application are authentic, non-hallucinated public-domain verse translations from accredited scholarly sources:

- **Aeneid (Books I–XII)**: Translated by **Theodore C. Williams** (1910). Published in Boston by Houghton Mifflin Co. Public Domain (published 1910; digitized by Perseus Digital Library, Tufts University, CC BY-SA 3.0 US).
- **Eclogues (Poems I–X)**: Translated by **James Rhoades** (1921). Published in *The Poems of Vergil*, London: Oxford University Press. Public Domain (published 1921; digitized by Perseus Digital Library, CC BY-SA 3.0 US).
- **Georgics (Books I–IV)**: Translated by **James Rhoades** (1921). Published in *The Poems of Vergil*, London: Oxford University Press. Public Domain (published 1921; digitized by Perseus Digital Library, CC BY-SA 3.0 US).
- *Historic Reference*: **John Dryden** (1697), *The Works of Virgil: Translated into English Verse*, Project Gutenberg EBook #228.

### Alignment & Fallback Protocol
- **Aligned Storage**: Structured JSON under `data/virgil/translation/{work}/book{book}.json` maps both standard Latin line cards and verse lines.
- **Strict No-Hallucination Policy**: When analyzing custom Latin or un-translated lines, the system never invents or generates a fluent translation. Instead, it falls back to the exact dictionary gloss sequence, clearly labeled:
  `"Literal gloss - no fluent translation available for this passage"`

### Endpoints
- `GET /virgil/translation?work=aeneid&book=1&start=1&end=11`: Returns aligned public-domain translation text, translator metadata, and per-line translations.
- `GET /virgil/read?work=aeneid&book=1`: Dedicated full-text reader view displaying the complete book with line numbers, Latin verse, and parallel English translation, with direct links back to the interactive analyzer.


