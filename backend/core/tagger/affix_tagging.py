import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Path to resources
RESOURCES_DIR = Path(__file__).resolve().parent.parent.parent / "resources"

# Dialect file mappings
DIALECT_FILES = {
    "ilocano": {
        "rules": "Ilocano-rules.json",
        "roots": "root_ilocano.json"
    },
    "cebuano": {
        "rules": "Cebuano-rules.json",
        "roots": "root_cebuano.json"
    },
    "hiligaynon": {
        "rules": "Hiligaynon-rules.json",
        "roots": "root_hiligaynon.json"
    }
}

# Cache for loaded resources
_rules_cache: Dict[str, Dict] = {}
_roots_cache: Dict[str, Dict] = {}


def load_rules(dialect: str) -> Dict:
    """Load affix rules for a dialect."""
    dialect = dialect.lower()
    
    if dialect in _rules_cache:
        return _rules_cache[dialect]
    
    if dialect not in DIALECT_FILES:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    rules_path = RESOURCES_DIR / DIALECT_FILES[dialect]["rules"]
    
    with open(rules_path, "r", encoding="utf-8") as f:
        rules = json.load(f)
    
    _rules_cache[dialect] = rules
    return rules


def load_roots(dialect: str) -> Dict:
    """Load root dictionary for a dialect."""
    dialect = dialect.lower()
    
    if dialect in _roots_cache:
        return _roots_cache[dialect]
    
    if dialect not in DIALECT_FILES:
        raise ValueError(f"Unsupported dialect: {dialect}")
    
    roots_path = RESOURCES_DIR / DIALECT_FILES[dialect]["roots"]
    
    with open(roots_path, "r", encoding="utf-8") as f:
        roots = json.load(f)
    
    _roots_cache[dialect] = roots
    return roots


def get_prefixes_by_pos(rules: Dict) -> Dict[str, List[str]]:
    """Extract prefixes grouped by POS from rules."""
    pos_prefixes = {}
    
    for pos, pos_rules in rules.items():
        if "prefix_rules" in pos_rules:
            prefixes = [r["prefix"] for r in pos_rules["prefix_rules"]]
            # Sort by length (longest first) for greedy matching
            pos_prefixes[pos] = sorted(prefixes, key=len, reverse=True)
    
    return pos_prefixes


def get_suffixes_by_pos(rules: Dict) -> Dict[str, List[str]]:
    """Extract suffixes grouped by POS from rules."""
    pos_suffixes = {}
    
    for pos, pos_rules in rules.items():
        if "suffix_rules" in pos_rules:
            suffixes = [r["suffix"] for r in pos_rules["suffix_rules"]]
            # Sort by length (longest first) for greedy matching
            pos_suffixes[pos] = sorted(suffixes, key=len, reverse=True)
    
    return pos_suffixes


def predict_pos_affix(token: str, dialect: str) -> str:
    """
    Predict POS tag for a token using affix-based rules.
    
    Priority:
    1. Root dictionary lookup (exact match)
    2. Prefix pattern matching
    3. Suffix pattern matching
    4. Unknown
    
    Args:
        token: Word token (lowercase)
        dialect: Language dialect
        
    Returns:
        Predicted POS tag
    """
    token = token.lower()
    dialect = dialect.lower()
    
    # Handle punctuation
    if token in ".!?,;:":
        return "PUNCT"
    
    # Load resources
    rules = load_rules(dialect)
    roots = load_roots(dialect)
    
    # Step 1: Check root dictionary
    if token in roots:
        return roots[token]
    
    # Step 2: Check prefixes (longest match first)
    pos_prefixes = get_prefixes_by_pos(rules)
    
    for pos, prefixes in pos_prefixes.items():
        for prefix in prefixes:
            if token.startswith(prefix) and len(token) > len(prefix):
                return pos
    
    # Step 3: Check suffixes (longest match first)
    pos_suffixes = get_suffixes_by_pos(rules)
    
    for pos, suffixes in pos_suffixes.items():
        for suffix in suffixes:
            if token.endswith(suffix) and len(token) > len(suffix):
                return pos
    
    # Step 4: Unknown
    return "UNK"


def predict_pos_batch(tokens: List[str], dialect: str) -> List[str]:
    """
    Predict POS tags for a list of tokens.
    
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
