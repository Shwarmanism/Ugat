"""
CRF POS Tagger Training Script
Ugat-Lemmatizer Project

Trains CRF models for Philippine languages (Ilocano, Cebuano, Hiligaynon).
"""

import os
import sys
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from sklearn_crfsuite import CRF
from sklearn_crfsuite.metrics import flat_classification_report
from sklearn.model_selection import train_test_split


# ----------------------------
# Path Configuration
# ----------------------------
# Get absolute paths based on this file's location
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent.parent
RESOURCES_DIR = BACKEND_DIR / "resources"
MODELS_DIR = SCRIPT_DIR  # Save models in the same directory as this script


# ----------------------------
# Training Configuration
# ----------------------------
# Add or remove languages here - the script will automatically find files
# Format: "language_name": "data_filename" (without path)
LANGUAGE_CONFIGS: Dict[str, str] = {
    "ilocano": "ilocano_crf_formatted.txt",
    "cebuano": "Cebuano_crf_formatted.txt",
    "hiligaynon": "Hiligaynon_crf_formatted.txt",
}

# CRF Training Parameters
CRF_PARAMS = {
    "algorithm": "lbfgs",
    "c1": 0.1,
    "c2": 0.05,            # Lower L2 slightly
    "max_iterations": 200, # Increased from 100 to ensure convergence
    "all_possible_transitions": True,
}

# Data format settings
EXPECTED_COLUMNS = 7  # token + 5 features + label
SENTENCE_END_PUNCT = {".", "!", "?"}
TEST_SIZE = 0.2
RANDOM_STATE = 42


# ----------------------------
# Data Preprocessing
# ----------------------------
def get_sentence_fingerprint(sentence_features: List[Dict], labels: List[str]) -> str:
    """Create a unique signature for a sentence + its tags."""
    tokens = " ".join(feat["token"] for feat in sentence_features)
    tags = " ".join(labels)
    return f"{tokens}|||{tags}"

def deduplicate_sentences(
    sentences: List[List[Dict]], 
    labels: List[List[str]], 
    verbose: bool = True
) -> Tuple[List[List[Dict]], List[List[str]], Dict]:
    
    seen_fingerprints = set()
    unique_sentences = []
    unique_labels = []
    duplicate_count = 0
    
    for sent, lbl in zip(sentences, labels):
        # Pass BOTH sentence and label to fingerprint
        fingerprint = get_sentence_fingerprint(sent, lbl)
        
        if fingerprint not in seen_fingerprints:
            seen_fingerprints.add(fingerprint)
            unique_sentences.append(sent)
            unique_labels.append(lbl)
        else:
            duplicate_count += 1
    
    stats = {
        "original_count": len(sentences),
        "unique_count": len(unique_sentences),
        "duplicates_removed": duplicate_count,
    }
    
    if verbose and duplicate_count > 0:
        print(f"  ⚠ Deduplication: Removed {duplicate_count} duplicate sentences")
    
    return unique_sentences, unique_labels, stats


# ----------------------------
# Data Loading
# ----------------------------
def load_crf_data(file_path: Path, deduplicate: bool = True) -> Tuple[List[List[Dict]], List[List[str]]]:
    """
    Load CRF data with ENHANCED feature extraction for Philippine languages.
    """
    sentences = []
    labels = []
    current_sentence = []
    current_labels = []

    if not file_path.exists():
        raise FileNotFoundError(f"Data file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Sentence boundary
            if not line:
                if current_sentence:
                    sentences.append(current_sentence)
                    labels.append(current_labels)
                    current_sentence = []
                    current_labels = []
                continue

            cols = line.split("\t")
            # Relaxed check: allow lines that might have fewer cols if we can salvage the token/label
            if len(cols) < 2: 
                continue

            token = cols[0]
            # If your file format varies, adjust index -1 for label
            label = cols[-1]
            
            # --- FEATURE ENGINEERING START ---
            token_lower = token.lower()
            
            # Grab context from file columns if available, otherwise default
            # (Assumes cols: token, lower, p3, s3, prev, next, label)
            prev_word = cols[4] if len(cols) >= 6 else "BOS"
            next_word = cols[5] if len(cols) >= 6 else "EOS"

            token_features = {
                # 1. Basic Identity
                "token": token,
                "lower": token_lower,
                
                # 2. Morphology (Crucial for Ilocano/Cebuano/Hiligaynon)
                "prefix2": token_lower[:2],  # Captures 'um', 'in', 'ka', 'ma'
                "prefix3": token_lower[:3],  # Captures 'nag', 'mag', 'pag'
                "suffix2": token_lower[-2:], # Captures 'an', 'on', 'in'
                "suffix3": token_lower[-3:], # Captures 'han', 'hon'
                
                # 3. Orthography & patterns
                "is_first": len(current_sentence) == 0,
                "is_last": False, # We can't know this yet, usually handled by 'next_word' being EOS
                "is_capitalized": token[0].isupper(),
                "is_all_caps": token.isupper(),
                "is_numeric": token.isdigit(),
                "has_hyphen": "-" in token, # CRITICAL for "nag-", "taga-", "maka-"
                
                # 4. Context Window (The "neighbors")
                "prev_word": prev_word,
                "next_word": next_word,
                "prev_is_marker": prev_word.lower() in ["ti", "ni", "ang", "si", "ug", "sang", "sa", "iti"],
            }
            # --- FEATURE ENGINEERING END ---

            current_sentence.append(token_features)
            current_labels.append(label)

            if token in SENTENCE_END_PUNCT:
                sentences.append(current_sentence)
                labels.append(current_labels)
                current_sentence = []
                current_labels = []

    if current_sentence:
        sentences.append(current_sentence)
        labels.append(current_labels)

    if deduplicate and sentences:
        sentences, labels, _ = deduplicate_sentences(sentences, labels)

    return sentences, labels


# ----------------------------
# Model Training
# ----------------------------
def train_model(language: str, data_file: Path, model_path: Path, verbose: bool = True) -> Optional[CRF]:
   
    print("\n" + "=" * 60)
    print(f"  Training: {language.upper()}")
    print("=" * 60)
    print(f"  Data file: {data_file}")
    print(f"  Model output: {model_path}")

    try:
        # Load data
        X, y = load_crf_data(data_file)
        
        if not X:
            print(f"  ✗ ERROR: No sentences loaded from {data_file}")
            return None
            
        print(f"  ✓ Loaded {len(X)} sentences")

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE
        )
        print(f"  ✓ Split: {len(X_train)} train, {len(X_test)} test")

        # Train CRF
        print(f"  ⏳ Training CRF model...")
        crf = CRF(**CRF_PARAMS)
        crf.fit(X_train, y_train)
        print(f"  ✓ Training complete")

        # Evaluate
        y_pred = crf.predict(X_test)
        
        if verbose:
            print("\n  Classification Report:")
            print("  " + "-" * 50)
            report = flat_classification_report(y_test, y_pred, digits=3)
            # Indent the report
            for line in report.split('\n'):
                print(f"  {line}")

        # Save model
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(crf, f)
        print(f"\n  ✓ Model saved to: {model_path}")
        
        return crf

    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return None


def get_available_datasets() -> Dict[str, Path]:

    available = {}
    
    for lang, filename in LANGUAGE_CONFIGS.items():
        file_path = RESOURCES_DIR / filename
        if file_path.exists():
            available[lang] = file_path
            
    return available


def list_datasets():
    """Print available datasets and their status."""
    print("\n" + "=" * 60)
    print("  Available Language Datasets")
    print("=" * 60)
    
    for lang, filename in LANGUAGE_CONFIGS.items():
        file_path = RESOURCES_DIR / filename
        model_path = MODELS_DIR / f"{lang}_model.pkl"
        
        exists = "✓" if file_path.exists() else "✗"
        model_exists = "✓" if model_path.exists() else "✗"
        
        print(f"\n  {lang.upper()}")
        print(f"    Data file [{exists}]: {filename}")
        print(f"    Model [{model_exists}]: {lang}_model.pkl")
        
        if file_path.exists():
            # Count lines/sentences
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = sum(1 for _ in f)
            print(f"    Lines: {lines}")


def train_all_languages(languages: Optional[List[str]] = None, verbose: bool = True):
    
    available = get_available_datasets()
    
    if not available:
        print("✗ No datasets found in resources directory!")
        print(f"  Looking in: {RESOURCES_DIR}")
        return
    
    # Filter to requested languages if specified
    if languages:
        available = {k: v for k, v in available.items() if k in languages}
        
        # Check for missing requested languages
        missing = set(languages) - set(available.keys())
        if missing:
            print(f"⚠ Warning: Datasets not found for: {', '.join(missing)}")
    
    if not available:
        print("✗ No matching datasets to train!")
        return
    
    print(f"\n{'='*60}")
    print(f"  Training {len(available)} language model(s)")
    print(f"{'='*60}")
    
    results = {}
    for lang, data_path in available.items():
        model_path = MODELS_DIR / f"{lang}_model.pkl"
        model = train_model(lang, data_path, model_path, verbose)
        results[lang] = model is not None
    
    # Summary
    print("\n" + "=" * 60)
    print("  Training Summary")
    print("=" * 60)
    for lang, success in results.items():
        status = "✓ Success" if success else "✗ Failed"
        print(f"  {lang.capitalize()}: {status}")
    
    success_count = sum(results.values())
    print(f"\n  Total: {success_count}/{len(results)} models trained successfully")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CRF POS Tagger Training")
    print("  Ugat-Lemmatizer Project")
    print("=" * 60)
    print(f"  Resources: {RESOURCES_DIR}")
    print(f"  Models: {MODELS_DIR}")
    
    # Train all 3 languages
    train_all_languages()
    
    print("\n✓ Done!\n")


