import json
from pathlib import Path
from typing import Dict, List, Any

from core import (
    # Preprocessing
    tokenizer,
    segmenter,
    # Tagging
    crf_predict,
    affix_predict,
    format_tokens_for_crf,
    get_available_dialects,
    # Morphology
    get_morph_engine,
    lemmatize,
)

# ─────────────────────────────────────────────────────────────────────────────
# Path Configuration
# ─────────────────────────────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = _BACKEND_DIR / "results"
RESOURCES_DIR = _BACKEND_DIR / "resources"

# ─────────────────────────────────────────────────────────────────────────────
# Resource Configuration
# ─────────────────────────────────────────────────────────────────────────────
SUPPORTED_DIALECTS = frozenset({"ilocano", "cebuano", "hiligaynon"})

IRREGULAR_FILES = {
    "ilocano": "irregular_ilocano.json",
    "cebuano": "irregular_cebuano.json",
    "hiligaynon": "irregular_hiligaynon.json",
}

ROOT_FILES = {
    "ilocano": "root_ilocano.json",
    "cebuano": "root_cebuano.json",
    "hiligaynon": "root_hiligaynon.json",
}

# Function word POS tags that skip morphology - frozen for O(1) lookup
FUNCTION_WORD_POS = frozenset({"DET", "CONJ", "PRON", "PUNCT", "ADP", "NUM"})

# ─────────────────────────────────────────────────────────────────────────────
# Cache Management
# ─────────────────────────────────────────────────────────────────────────────
_irregular_cache: Dict[str, Dict] = {}
_root_cache: Dict[str, Dict] = {}
_root_set_cache: Dict[str, frozenset] = {}  # For O(1) lookups
_initialized = False


def load_irregular(dialect: str) -> Dict:
    """Load irregular word dictionary for a dialect. Cached after first load."""
    dialect = dialect.lower()
    
    # Fast path: return cached
    if dialect in _irregular_cache:
        return _irregular_cache[dialect]
    
    # Validate dialect
    if dialect not in SUPPORTED_DIALECTS:
        return {}
    
    file_path = RESOURCES_DIR / IRREGULAR_FILES[dialect]
    if not file_path.exists():
        _irregular_cache[dialect] = {}  # Cache empty to avoid re-checking
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        _irregular_cache[dialect] = json.load(f)
    
    return _irregular_cache[dialect]


def load_roots(dialect: str) -> Dict:
    """Load root word dictionary for a dialect. Cached after first load."""
    dialect = dialect.lower()
    
    # Fast path: return cached
    if dialect in _root_cache:
        return _root_cache[dialect]
    
    # Validate dialect
    if dialect not in SUPPORTED_DIALECTS:
        return {}
    
    file_path = RESOURCES_DIR / ROOT_FILES[dialect]
    if not file_path.exists():
        _root_cache[dialect] = {}  # Cache empty to avoid re-checking
        _root_set_cache[dialect] = frozenset()
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        _root_cache[dialect] = json.load(f)
    
    # Pre-build frozenset for O(1) lookups
    _root_set_cache[dialect] = frozenset(_root_cache[dialect].keys())
    
    return _root_cache[dialect]


def get_root_set(dialect: str) -> frozenset:
    """Get frozenset of root words for O(1) membership testing."""
    dialect = dialect.lower()
    if dialect not in _root_set_cache:
        load_roots(dialect)  # This will populate _root_set_cache
    return _root_set_cache.get(dialect, frozenset())


def preload_all() -> None:
    """
    Preload all resources into cache at startup.
    Call this once when server starts to warm caches.
    """
    global _initialized
    if _initialized:
        return
    
    print("[INFO] Preloading resources...")
    
    for dialect in SUPPORTED_DIALECTS:
        load_irregular(dialect)
        load_roots(dialect)
    
    # Initialize morphology engine (singleton)
    get_morph_engine()
    
    _initialized = True
    print("[OK] All resources preloaded")


def text_preprocess(raw_text, lang):
    """Step 1: Segment and tokenize raw text."""
    processed_text = []

    sentences = segmenter(raw_text)

    for sentence in sentences:
        tokens = tokenizer(sentence)
        processed_text.append(tokens)

    return {
        "lang": lang,
        "sentences": processed_text
    }


def pos_tagging(preprocessed_data):

    lang = preprocessed_data["lang"].lower()
    sentences = preprocessed_data["sentences"]
    
    crf_tagged = []
    affix_tagged = []
    
    for tokens in sentences:
        # CRF-based tagging
        features = format_tokens_for_crf(tokens)
        crf_tags = list(crf_predict(features, lang))
        crf_tagged.append(list(zip(tokens, crf_tags)))
        
        # Affix-based tagging
        affix_tags = affix_predict(tokens, lang)
        affix_tagged.append(list(zip(tokens, affix_tags)))
    
    return {
        "lang": lang,
        "sentences": sentences,
        "crf_tagged": crf_tagged,
        "affix_tagged": affix_tagged
    }


def save_results(tagged_data, filename="pipeline_results.json"):
    output_path = OUTPUT_DIR / filename

    result = {
        "lang": tagged_data["lang"],
        "sentences": tagged_data["sentences"],
        "crf_results": [
            {"tokens": [t for t, _ in sent], "pos_tags": [p for _, p in sent]}
            for sent in tagged_data["crf_tagged"]
        ],
        "affix_results": [
            {"tokens": [t for t, _ in sent], "pos_tags": [p for _, p in sent]}
            for sent in tagged_data["affix_tagged"]
        ]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    return output_path


# Cached engine reference for morph_rules
_morph_engine = None


def morph_rules(token: str, pos: str, lang: str) -> Dict[str, Any]:
    """
    Apply POS-aware morphological analysis using FSM-based affix stripping.
    
    The POS tag is passed to the engine so that:
    1. Only rules for that POS are applied (VERB rules for VERB, etc.)
    2. Candidate lemma must match the same POS in the root dictionary
    """
    global _morph_engine
    if _morph_engine is None:
        _morph_engine = get_morph_engine()
    
    # Pass POS to engine for POS-aware rule selection and validation
    result = _morph_engine.lemmatize(token, lang, pos)
    
    return {
        "token": token,
        "root": result["lemma"],
        "pos": result.get("pos", pos),  # Use engine's POS if available
        "affixes": result.get("affixes", []),
        "rule": result.get("rule", "None"),
        "status": result.get("status", "not_found")
    }


def process_tokens(tagged_data: Dict, mode: str = "crf") -> Dict:
    """
    Process each token: check irregular, check root, check function word, apply morphology.
    
    Flow for each token:
    1. Is it irregular? → Get root from irregular dictionary
    2. Is it a root word? → Keep original token
    3. Is it a function word (DET, CONJ, PRON, PUNCT, etc.)? → Keep original
    4. None of above → Apply morphology rules
    """
    lang = tagged_data["lang"].lower()
    
    # Pre-fetch dictionaries (cached) - avoid repeated lookups
    irregular_dict = load_irregular(lang)
    root_dict = load_roots(lang)
    root_set = get_root_set(lang)  # O(1) membership testing
    
    processed_sentences = []
    
    # Select tags based on mode
    source_tags = tagged_data["affix_tagged"] if mode == "affix" else tagged_data["crf_tagged"]

    for tagged_sent in source_tags:
        processed_tokens = []
        
        for token, pos in tagged_sent:
            # Token already lowercase from tokenizer, but ensure it
            token_lower = token.lower()
            
            # Check irregular first (most specific)
            if token_lower in irregular_dict:
                irregular_info = irregular_dict[token_lower]
                processed_tokens.append({
                    "token": token,
                    "type": "irregular",
                    "root": irregular_info.get("equivalent", token),
                    "pos": irregular_info.get("pos", pos),
                    "affixes": [],
                    "stripped": ""  # Irregular words usually don't have clean stripping
                })
            # Check root (O(1) frozenset lookup)
            elif token_lower in root_set:
                processed_tokens.append({
                    "token": token,
                    "type": "root",
                    "root": token_lower,
                    "pos": root_dict[token_lower],
                    "affixes": [],
                    "stripped": ""
                })
            # Check function word (O(1) frozenset lookup)
            # DET, CONJ, PRON, PUNCT, ADP, NUM - skip morphology
            elif pos in FUNCTION_WORD_POS:
                processed_tokens.append({
                    "token": token,
                    "type": "function",
                    "root": token_lower,
                    "pos": pos,
                    "affixes": [],
                    "stripped": ""
                })
            # Apply morphological analysis
            else:
                morph_result = morph_rules(token, pos, lang)
                # Use regex for case-insensitive replacement to handle "Nagbasa" -> "basa"
                import re
                stripped_content = re.sub(re.escape(morph_result["root"]), "", token, flags=re.IGNORECASE)
                print(f"DEBUG: Token='{token}', Root='{morph_result['root']}', Stripped='{stripped_content}'")
                
                # If specific affixes were found, try to reconstruct stripped from them if direct replace is messy
                # If specific affixes were found, try to reconstruct stripped from them if direct replace is messy
                if not stripped_content and morph_result["affixes"]:
                     # Simple heuristic: join affixes and remove hyphens
                     stripped_content = "".join(a.replace("-", "") for a in morph_result["affixes"])

                processed_tokens.append({
                    "token": token,
                    "type": "morphed",
                    "root": morph_result["root"],
                    "pos": morph_result["pos"],
                    "affixes": morph_result["affixes"],
                    "stripped": stripped_content
                })
        
        processed_sentences.append(processed_tokens)
    
    return {
        "lang": lang,
        "sentences": processed_sentences
    }


def main_pipeline(raw_text, lang, mode="crf"):
    """
    Complete NLP pipeline from raw text to lemmatization.
    """
    # Step 1: Preprocess
    preprocessed = text_preprocess(raw_text, lang)
    
    # Step 2: POS Tagging
    tagged = pos_tagging(preprocessed)
    
    # Step 3: Process each token (irregular check + morphology)
    processed = process_tokens(tagged, mode=mode)
    
    # Step 4: Build simple result
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "pipeline_results.json"
    
    tokens_summary = []
    for proc_sent in processed["sentences"]:
        for t in proc_sent:
            tokens_summary.append({
                "token": t["token"],
                "lemma": t["root"],
                "pos": t["pos"],
                "type": t["type"],
                "affixes": t.get("affixes", []),
                "stripped": t.get("stripped", "")
            })
    
    result = {
        "language": lang,
        "input": raw_text,
        "total_tokens": len(tokens_summary),
        "tokens": tokens_summary
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Results saved to {output_path.name}")
    return result

    
if __name__ == "__main__":
    # Quick test
    test_text = "Nagkaon ang bata sang tinapay."
    result = main_pipeline(test_text, "hiligaynon")
    
    print(f"\nInput: {test_text}")
    print(f"{'Token':<15} {'Lemma':<15} {'POS':<10} {'Type':<12}")
    print("-" * 55)
    for t in result["tokens"]:
        print(f"{t['token']:<15} {t['lemma']:<15} {t['pos']:<10} {t['type']:<12}")