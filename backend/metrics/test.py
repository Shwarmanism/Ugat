import sys
import os
import pandas as pd
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
sys.path.append(str(BACKEND_DIR))

try:
    from core.tagger.affix_tagging import predict_pos_batch
    from core.tagger.crf_tagging import predict_pos, format_tokens_for_crf
    # Import the engine directly to be safe
    from core.morphology.affix_stripping import get_morph_engine
    print("✅ Engine Loaded.")
except ImportError:
    sys.exit("❌ Could not load engine.")

# ─────────────────────────────────────────────────────────────────────────────
# 🧪 THE "TRAP" TEST CASES (Ambiguous Words)
# ─────────────────────────────────────────────────────────────────────────────
AMBIGUOUS_DATA = [
    # ILOCANO: "Agosto" (August) starts with "Ag-" (Verb prefix).
    # Trap: Ag-osto -> osto (Wrong)
    {
        "Dialect": "ILOCANO",
        "Sentence": "Naragsak ti Agosto idiay plaza .", 
        "Target_Word": "Agosto",
        "Expected_POS": "NOUN",  # or PROPN
        "Expected_Lemma": "agosto" 
    },
    
    # CEBUANO: "Manila" starts with "Ma-" (Adj/Verb prefix).
    # Trap: Ma-nila -> nila (Wrong)
    {
        "Dialect": "CEBUANO",
        "Sentence": "Moadto kami sa Manila ugma .",
        "Target_Word": "Manila",
        "Expected_POS": "NOUN", # or PROPN
        "Expected_Lemma": "manila"
    },

    # HILIGAYNON: "Magallanes" (Name) starts with "Mag-" (Verb prefix).
    # Trap: Mag-allanes -> allanes (Wrong)
    {
        "Dialect": "HILIGAYNON",
        "Sentence": "Si Magallanes ang nag-abot .",
        "Target_Word": "Magallanes",
        "Expected_POS": "NOUN", # or PROPN
        "Expected_Lemma": "magallanes"
    }
]

print(f"\n⚡ RUNNING AMBIGUITY STRESS TEST...")
print(f"{'DIALECT':<10} | {'WORD':<12} | {'MODEL':<8} | {'PRED POS':<8} | {'PRED LEMMA':<12} | {'STATUS'}")
print("-" * 80)

engine = get_morph_engine()
results = []

for case in AMBIGUOUS_DATA:
    dialect = case["Dialect"]
    sent = case["Sentence"]
    target = case["Target_Word"]
    correct_lemma = case["Expected_Lemma"].lower()
    
    tokens = sent.split()
    target_idx = tokens.index(target)

    # 1. RUN AFFIX PIPELINE
    affix_tags = predict_pos_batch(tokens, dialect)
    affix_tag = affix_tags[target_idx]
    
    # DIRECT CALL TO ENGINE CLASS METHOD
    affix_lemma_res = engine.lemmatize(target, dialect, pos=affix_tag)
    affix_lemma = affix_lemma_res["lemma"]

    # 2. RUN CRF PIPELINE
    feats = format_tokens_for_crf(tokens)
    crf_tags = predict_pos(feats, dialect)
    crf_tag = crf_tags[target_idx]
    
    # DIRECT CALL TO ENGINE CLASS METHOD
    crf_lemma_res = engine.lemmatize(target, dialect, pos=crf_tag)
    crf_lemma = crf_lemma_res["lemma"]

    # 3. PRINT RESULTS
    # Check Affix
    status_affix = "✅ PASS" if affix_lemma == correct_lemma else "❌ FAIL"
    print(f"{dialect:<10} | {target:<12} | {'AFFIX':<8} | {affix_tag:<8} | {affix_lemma:<12} | {status_affix}")
    
    # Check CRF
    status_crf = "✅ PASS" if crf_lemma == correct_lemma else "❌ FAIL"
    print(f"{'':<10} | {'':<12} | {'CRF':<8} | {crf_tag:<8} | {crf_lemma:<12} | {status_crf}")
    print("-" * 80)
    
    results.append({"Model": "Affix", "Score": 1 if affix_lemma == correct_lemma else 0})
    results.append({"Model": "CRF", "Score": 1 if crf_lemma == correct_lemma else 0})

# ─────────────────────────────────────────────────────────────────────────────
# 📊 FINAL SCORE SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
df = pd.DataFrame(results)
summary = df.groupby("Model")["Score"].mean()
print("\n📈 FINAL ACCURACY ON AMBIGUOUS CASES:")
print(summary)