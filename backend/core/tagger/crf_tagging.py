import pickle
from pathlib import Path
from typing import List, Dict

# Path to trained models
MODELS_DIR = Path(__file__).resolve().parent

# Available dialects and their model files
DIALECT_MODELS = {
    "ilocano": "ilocano_model.pkl",
    "cebuano": "cebuano_model.pkl",
    "hiligaynon": "hiligaynon_model.pkl",
}

# Cache for loaded models (avoid reloading)
_model_cache: Dict[str, object] = {}


def get_available_dialects() -> List[str]:
    """Return list of available dialects with trained models."""
    available = []
    for dialect, model_file in DIALECT_MODELS.items():
        if (MODELS_DIR / model_file).exists():
            available.append(dialect)
    return available


def load_model(dialect: str):
    
    dialect = dialect.lower()
    
    if dialect not in DIALECT_MODELS:
        raise ValueError(f"Unsupported dialect: {dialect}. Available: {list(DIALECT_MODELS.keys())}")
    
    # Return cached model if available
    if dialect in _model_cache:
        return _model_cache[dialect]
    
    model_path = MODELS_DIR / DIALECT_MODELS[dialect]
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model not found for {dialect}. Run train_models.py first. "
            f"Expected: {model_path}"
        )
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    _model_cache[dialect] = model
    return model


def predict_pos(features: List[Dict], dialect: str) -> List[str]:
    
    if not features:
        return []
    
    model = load_model(dialect)
    
    # CRF expects list of sentences, wrap in list and return first result
    predictions = model.predict([features])[0]
    
    return predictions


def format_tokens_for_crf(tokens: List[str]) -> List[Dict]:

    features = []
    
    for i, token in enumerate(tokens):
        prev_word = tokens[i - 1] if i > 0 else "BOS"
        next_word = tokens[i + 1] if i < len(tokens) - 1 else "EOS"
        
        token_features = {
            "token": token,
            "lower": token.lower(),
            "prefix3": token[:3].lower() if len(token) >= 3 else token.lower(),
            "suffix3": token[-3:].lower() if len(token) >= 3 else token.lower(),
            "prev_word": prev_word,
            "next_word": next_word,
            "is_title": token.istitle(),
            "is_upper": token.isupper(),
            "is_digit": token.isdigit(),
            "length": str(len(token)),
        }
        features.append(token_features)
    
    return features


if __name__ == "__main__":
    import json
    
    # Load test input
    test_file = MODELS_DIR / "test_input.json"
    
    with open(test_file, "r", encoding="utf-8") as f:
        test_data = json.load(f)
    
    dialect = test_data["selected_dialect"]
    tokens = test_data["tokens"]
    sentence = test_data.get("sentence", "")
    
    print("=" * 50)
    print("  CRF POS Tagger Test")
    print("=" * 50)
    print(f"\n  Dialect: {dialect}")
    print(f"  Sentence: {sentence}")
    print(f"  Tokens: {tokens}")
    
    # Format tokens for CRF
    features = format_tokens_for_crf(tokens)
    
    # Predict POS tags
    pos_tags = predict_pos(features, dialect)
    
    # Add pos_tags to the data (convert to list for JSON serialization)
    test_data["crf_tags"] = list(pos_tags)
    
    # Save updated JSON
    with open(test_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=4, ensure_ascii=False)
    
    print("\n  Results:")
    print("  " + "-" * 30)
    for i, (token, pos) in enumerate(zip(tokens, pos_tags)):
        print(f"    [{i}] {token:15} → {pos}")
    
    print(f"\n  ✓ Updated {test_file.name} with pos_tags")
