import json
from pathlib import Path
from core import (
    tokenizer,
    segmenter,
    crf_predict,
    affix_predict,
    format_tokens_for_crf,
    get_available_dialects,
)

# Output path
OUTPUT_DIR = Path(__file__).resolve().parent / "core" / "results"
RESOURCES_DIR = Path(__file__).resolve().parent / "resources"

# Irregular word files per dialect
IRREGULAR_FILES = {
    "ilocano": "irregular_ilocano.json",
    "cebuano": "irregular_cebuano.json",
    "hiligaynon": "irregular_hiligaynon.json",
}

# Root dictionary files per dialect
ROOT_FILES = {
    "ilocano": "root_ilocano.json",
    "cebuano": "root_cebuano.json",
    "hiligaynon": "root_hiligaynon.json",
}

# Cache for irregular and root dictionaries
_irregular_cache = {}
_root_cache = {}


def load_irregular(dialect: str) -> dict:
    """Load irregular word dictionary for a dialect."""
    dialect = dialect.lower()
    
    if dialect in _irregular_cache:
        return _irregular_cache[dialect]
    
    if dialect not in IRREGULAR_FILES:
        return {}
    
    file_path = RESOURCES_DIR / IRREGULAR_FILES[dialect]
    
    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        irregular = json.load(f)
    
    _irregular_cache[dialect] = irregular
    return irregular


def load_roots(dialect: str) -> dict:
    """Load root word dictionary for a dialect."""
    dialect = dialect.lower()
    
    if dialect in _root_cache:
        return _root_cache[dialect]
    
    if dialect not in ROOT_FILES:
        return {}
    
    file_path = RESOURCES_DIR / ROOT_FILES[dialect]
    
    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        roots = json.load(f)
    
    _root_cache[dialect] = roots
    return roots


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


def morph_rules(token, pos, lang):

    # TODO: Implement actual morphological analysis
    # For now, return the token as-is
    return {
        "token": token,
        "root": token,  # Placeholder - will be replaced with actual root extraction
        "pos": pos,
        "affixes": []   # Placeholder - will contain extracted affixes
    }


# Function word POS tags - these don't need morphological analysis
FUNCTION_WORD_POS = {"DET", "CONJ", "PRON", "PUNCT", "ADP", "PART", "NUM"}


def process_tokens(tagged_data):
    """
    Process each token: check irregular, check root, check function word, apply morphology.
    
    Flow for each token:
    1. Is it irregular? → Get root from irregular dictionary
    2. Is it a root word? → Keep original token
    3. Is it a function word (DET, CONJ, PRON, PUNCT, etc.)? → Keep original
    4. None of above → Apply morphology rules
    """
    lang = tagged_data["lang"].lower()
    
    # Load dictionaries for this dialect
    irregular_dict = load_irregular(lang)
    root_dict = load_roots(lang)
    
    processed_sentences = []
    
    # Use CRF tags as primary
    for sent_idx, tagged_sent in enumerate(tagged_data["crf_tagged"]):
        processed_tokens = []
        
        for token, pos in tagged_sent:
            token_lower = token.lower()
            
            if token_lower in irregular_dict:
                # 1. Token is irregular - get equivalent from lexicon
                irregular_info = irregular_dict[token_lower]
                processed_tokens.append({
                    "token": token,
                    "type": "irregular",
                    "root": irregular_info.get("equivalent", token),
                    "pos": irregular_info.get("pos", pos),
                    "affixes": []
                })
            elif token_lower in root_dict:
                # 2. Token is a root word - keep original
                processed_tokens.append({
                    "token": token,
                    "type": "root",
                    "root": token_lower,
                    "pos": root_dict[token_lower],
                    "affixes": []
                })
            elif pos in FUNCTION_WORD_POS:
                # 3. Token is a function word - keep original
                processed_tokens.append({
                    "token": token,
                    "type": "function",
                    "root": token_lower,
                    "pos": pos,
                    "affixes": []
                })
            else:
                # 4. Token needs morphological analysis
                morph_result = morph_rules(token, pos, lang)
                processed_tokens.append({
                    "token": token,
                    "type": "morphed",
                    "root": morph_result["root"],
                    "pos": morph_result["pos"],
                    "affixes": morph_result["affixes"]
                })
        
        processed_sentences.append(processed_tokens)
    
    return {
        "lang": lang,
        "sentences": processed_sentences
    }


def main_pipeline(raw_text, lang):
    """
    Complete NLP pipeline from raw text to lemmatization.
    
    Flow:
    1. Preprocess (segment + tokenize)
    2. POS Tagging (CRF + Affix)
    3. Process tokens (irregular check + morphology)
    4. Save results
    """
    # Step 1: Preprocess
    preprocessed = text_preprocess(raw_text, lang)
    
    # Step 2: POS Tagging
    tagged = pos_tagging(preprocessed)
    
    # Step 3: Process each token (irregular check + morphology)
    processed = process_tokens(tagged)
    
    # Step 4: Save results
    output_path = OUTPUT_DIR / "pipeline_results.json"
    
    result = {
        "lang": processed["lang"],
        "input": raw_text,
        "sentences": processed["sentences"]
    }
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    print(f"✓ Results saved to {output_path.name}")
    return result

    
if __name__ == "__main__":
    # Test the full pipeline
    text = "Napan ti lalaki idiay merkado."
    lang = "ilocano"

    print("=" * 60)
    print("  Main Pipeline Test")
    print("=" * 60)
    print(f"\n  Input: {text}")
    print(f"  Dialect: {lang}")
    
    # Run full pipeline
    result = main_pipeline(text, lang)
    
    # Display results
    print("\n  Processed Tokens:")
    print("  " + "-" * 55)
    print(f"    {'Token':<15} {'Type':<10} {'Root':<15} {'POS'}")
    print("  " + "-" * 55)
    for sent in result["sentences"]:
        for t in sent:
            print(f"    {t['token']:<15} {t['type']:<10} {t['root']:<15} {t['pos']}")