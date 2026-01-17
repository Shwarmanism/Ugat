import json
from pathlib import Path
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Path Configuration
# ─────────────────────────────────────────────────────────────────────────────
RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"

DIALECT_FILES = {
    "ilocano": {"rules": "Ilocano-rules.json", "roots": "root_ilocano.json"},
    "cebuano": {"rules": "Cebuano-rules.json", "roots": "root_cebuano.json"},
    "hiligaynon": {"rules": "Hiligaynon-rules.json", "roots": "root_hiligaynon.json"},
}

SUPPORTED_DIALECTS = frozenset(DIALECT_FILES.keys())

# ─────────────────────────────────────────────────────────────────────────────
# Cache - All resources loaded once and reused
# ─────────────────────────────────────────────────────────────────────────────
_rules_cache: Dict[str, Dict] = {}
_roots_cache: Dict[str, Dict] = {}
_prefixes_cache: Dict[str, Dict[str, Tuple[str, ...]]] = {}  # Pre-sorted tuples
_suffixes_cache: Dict[str, Dict[str, Tuple[str, ...]]] = {}


def load_rules(dialect: str) -> Dict:
    """Load affix rules for a dialect. Cached after first load."""
    dialect = dialect.lower()
    
    if dialect in _rules_cache:
        return _rules_cache[dialect]
    
    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    rules_path = RESOURCES_DIR / DIALECT_FILES[dialect]["rules"]
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    
    _rules_cache[dialect] = rules
    
    # Pre-compute and cache prefix/suffix lookups
    _build_affix_caches(dialect, rules)
    
    return rules


def load_roots(dialect: str) -> Dict:
    """Load root dictionary for a dialect. Cached after first load."""
    dialect = dialect.lower()
    
    if dialect in _roots_cache:
        return _roots_cache[dialect]
    
    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    roots_path = RESOURCES_DIR / DIALECT_FILES[dialect]["roots"]
    
    with open(roots_path, "r", encoding="utf-8") as f:
        _roots_cache[dialect] = json.load(f)
    
    return _roots_cache[dialect]


def _build_affix_caches(dialect: str, rules: Dict) -> None:
    """Pre-build sorted affix tuples for fast lookup."""
    pos_prefixes = {}
    pos_suffixes = {}
    
    for pos, pos_rules in rules.items():
        if isinstance(pos_rules, dict):
            # Extract and sort prefixes (longest first)
            if "prefix_rules" in pos_rules:
                prefixes = [r["prefix"] for r in pos_rules["prefix_rules"] if "prefix" in r]
                pos_prefixes[pos] = tuple(sorted(prefixes, key=len, reverse=True))
            
            # Extract and sort suffixes (longest first)
            if "suffix_rules" in pos_rules:
                suffixes = [r["suffix"] for r in pos_rules["suffix_rules"] if "suffix" in r]
                pos_suffixes[pos] = tuple(sorted(suffixes, key=len, reverse=True))
    
    _prefixes_cache[dialect] = pos_prefixes
    _suffixes_cache[dialect] = pos_suffixes


def get_prefixes_by_pos(dialect: str) -> Dict[str, Tuple[str, ...]]:
    """Get cached prefixes grouped by POS. Pre-sorted by length (longest first)."""
    if dialect not in _prefixes_cache:
        load_rules(dialect)  # This will populate the cache
    return _prefixes_cache.get(dialect, {})


def get_suffixes_by_pos(dialect: str) -> Dict[str, Tuple[str, ...]]:
    """Get cached suffixes grouped by POS. Pre-sorted by length (longest first)."""
    if dialect not in _suffixes_cache:
        load_rules(dialect)  # This will populate the cache
    return _suffixes_cache.get(dialect, {})


# Punctuation set for O(1) lookup
_PUNCT_CHARS = frozenset(".!?,;:")


def predict_pos_affix(token: str, dialect: str) -> str:
    """
    Predict POS tag for a token using affix-based rules.
    
    Priority:
    1. Punctuation check
    2. Root dictionary lookup (exact match)
    3. Prefix pattern matching (longest first)
    4. Suffix pattern matching (longest first)
    5. Unknown
    
    Args:
        token: Word token
        dialect: Language dialect
        
    Returns:
        Predicted POS tag
    """
    token_lower = token.lower()
    dialect = dialect.lower()
    
    # Fast path: punctuation
    if token_lower in _PUNCT_CHARS:
        return "PUNCT"
    
    # Load cached resources
    roots = load_roots(dialect)
    
    # Step 1: Check root dictionary (exact match)
    if token_lower in roots:
        return roots[token_lower]
    
    # Get cached affix lookups (pre-sorted by length)
    pos_prefixes = get_prefixes_by_pos(dialect)
    pos_suffixes = get_suffixes_by_pos(dialect)
    token_len = len(token_lower)
    
    # Step 2: Check prefixes (longest match first)
    for pos, prefixes in pos_prefixes.items():
        for prefix in prefixes:
            if token_len > len(prefix) and token_lower.startswith(prefix):
                return pos
    
    # Step 3: Check suffixes (longest match first)
    for pos, suffixes in pos_suffixes.items():
        for suffix in suffixes:
            if token_len > len(suffix) and token_lower.endswith(suffix):
                return pos
    
    return "UNK"


def predict_pos_batch(tokens: List[str], dialect: str) -> List[str]:
    """
    Predict POS tags for a list of tokens efficiently.
    Pre-loads caches once then processes all tokens.
    
    Args:
        tokens: List of word tokens
        dialect: Language dialect
        
    Returns:
        List of predicted POS tags
    """
    return [predict_pos_affix(token, dialect) for token in tokens]


if __name__ == "__main__":
    # Load test input (same format as CRF)
    TAGGER_DIR = Path(__file__).resolve().parent
    test_file = TAGGER_DIR / "test_input.json"
    output_file = TAGGER_DIR / "affix_tags.json"
    
    with open(test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    dialect = test_data["selected_dialect"]
    tokens = test_data["tokens"]
    sentence = test_data.get("sentence", "")
    
    print("=" * 50)
    print("  Affix-Based POS Tagger Test")
    print("=" * 50)
    print(f"\n  Dialect: {dialect}")
    print(f"  Sentence: {sentence}")
    print(f"  Tokens: {tokens}")
    
    # Predict POS tags
    pos_tags = predict_pos_batch(tokens, dialect)
    
    # Save results to affix_tags.json
    output_data = {
        "selected_dialect": dialect,
        "tokens": tokens,
        "sentence": sentence,
        "pos_tags": pos_tags
    }
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    print("\n  Results:")
    print("  " + "-" * 30)
    for i, (token, pos) in enumerate(zip(tokens, pos_tags)):
        print(f"    [{i}] {token:15} → {pos}")
    
    print(f"\n  ✓ Saved to {output_file.name}")
