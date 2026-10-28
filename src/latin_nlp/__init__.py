"""Latin NLP: lexer -> morphology -> dictionary -> parser pipeline.

Public entry points:
  from latin_nlp.pipeline import analyze_text, parse_text
  from latin_nlp.lexicon import load_lexicon
  from latin_nlp.morphology import MorphAnalyzer
"""

from .pipeline import analyze_text, parse_text

__all__ = ["analyze_text", "parse_text"]
__version__ = "0.2.0"
