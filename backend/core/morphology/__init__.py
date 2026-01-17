from .affix_stripping import MorphologicalEngine

# Singleton instance for convenience
_engine = None

def get_engine():
    """Get or create the morphological engine singleton."""
    global _engine
    if _engine is None:
        _engine = MorphologicalEngine()
    return _engine

def lemmatize(word, lang="ilocano"):
    """Quick lemmatization function."""
    return get_engine().lemmatize(word, lang)

def is_root(word, lang="ilocano"):
    """Check if word is a root word."""
    return get_engine().is_root(word, lang)

__all__ = [
    "MorphologicalEngine",
    "get_engine",
    "lemmatize",
    "is_root",
]
