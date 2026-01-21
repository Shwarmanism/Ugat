import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix
import warnings
import sys
import os
import json
import numpy as np
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP & PATHS
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
sys.path.append(str(BACKEND_DIR))
RESOURCES_DIR = BACKEND_DIR / "resources"
OUTPUT_DIR = BACKEND_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📂 Execution Context: {BACKEND_DIR}")

# Import Engine
try:
    from core.tagger.affix_tagging import predict_pos_batch
    from core.tagger.crf_tagging import predict_pos, format_tokens_for_crf
    from core import lemmatize
    print("✅ Backend Engine Loaded!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# 2. HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
FUNCTION_WORD_POS = frozenset({"DET", "CONJ", "PRON", "PUNCT", "ADP", "NUM", "ADV", "PART", "DEM"})

def load_irregular(dialect):
    path = RESOURCES_DIR / f"irregular_{dialect.lower()}.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

def get_root_set(dialect):
    path = RESOURCES_DIR / f"root_{dialect.lower()}.json"
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f: return set(json.load(f).keys())
    return set()

def smart_lemmatize(token, pos_tag, dialect):
    token_lower = token.lower()
    
    # 1. Check Irregular
    irregular_dict = load_irregular(dialect)
    if token_lower in irregular_dict:
        return irregular_dict[token_lower].get("equivalent", token_lower)

    # 2. Check Root
    root_set = get_root_set(dialect)
    if token_lower in root_set:
        return token_lower

    # 3. Check Function Words
    if pos_tag in FUNCTION_WORD_POS:
        return token_lower

    # 4. Apply Morphology
    try:
        result = lemmatize(token, pos=pos_tag, dialect=dialect)
        if isinstance(result, dict):
            return result.get("lemma", token_lower)
        return result
    except Exception:
        return token_lower

# ─────────────────────────────────────────────────────────────────────────────
# 3. TEST DATA
# ─────────────────────────────────────────────────────────────────────────────
TEST_DATA = {
    "ILOCANO": [
        ("Napan da idiay balay .", ["VERB", "PRON", "DEM", "NOUN", "PUNCT"], ["mapan", "isúda", "diay", "balay", "."]),
        ("Agbuybuya dagiti ubbing iti plaza .", ["VERB", "DET", "NOUN", "ADP", "NOUN", "PUNCT"], ["buya", "dagiti", "ubing", "iti", "plaza", "."]),
        ("Agkatkatawa ti lalaki idiay balay .", ["VERB", "DET", "NOUN", "ADP", "NOUN", "PUNCT"], ["katawa", "ti", "lalaki", "diay", "balay", "."]),
        ("Nagkatawa dagiti ub-ubbing .", ["VERB", "DET", "NOUN", "PUNCT"], ["katawa", "dagiti", "ubing", "."]),
        ("Ag-agawid kami no malpas ti trabaho .", ["VERB", "PRON", "CONJ", "VERB", "DET", "NOUN", "PUNCT"], ["awid", "kami", "no", "malpas", "ti", "trabaho", "."]),
        ("Ginatangna ti dakkel a tinapay .", ["VERB", "DET", "ADJ", "PART", "NOUN", "PUNCT"], ["gatang", "ti", "dakkel", "a", "tinapay", "."]),
        ("Linuto da ti manok para kenkuana .", ["VERB", "PRON", "DET", "NOUN", "ADP", "PRON", "PUNCT"], ["luto", "da", "ti", "manok", "para", "kenkuana", "."]),
        ("Nu agturposka , agtrabahoka idiay Manila .", ["CONJ", "VERB", "PUNCT", "VERB", "ADP", "NOUN", "PUNCT"], ["nu", "turpos", ",", "trabaho", "diay", "manila", "."]),
        ("Kayatko nga agbasa ti libro ngem awan ti oras .", ["VERB", "PART", "VERB", "DET", "NOUN", "CONJ", "ADV", "DET", "NOUN", "PUNCT"], ["kayat", "nga", "basa", "ti", "libro", "ngem", "awan", "ti", "oras", "."]),
        ("Tumatayab ti manok .", ["VERB", "DET", "NOUN", "PUNCT"], ["tayab", "ti", "manok", "."]),
        ("Nangus-usar da ti lapis .", ["VERB", "PRON", "DET", "NOUN", "PUNCT"], ["usar", "isúda", "ti", "lapis", "."]),
        ("Naggugudua da .", ["VERB", "PRON", "PUNCT"], ["agduadua", "isúda", "."]),
    ],
    "CEBUANO": [
        ("Palita ang tinapay .", ["VERB", "DET", "NOUN", "PUNCT"], ["palit", "ang", "tinapay", "."]),
        ("Dad-a ang bata .", ["VERB", "DET", "NOUN", "PUNCT"], ["dala", "ang", "bata", "."]),
        ("Kan-a ang sud-an .", ["VERB", "DET", "NOUN", "PUNCT"], ["kaon", "ang", "sula", "."]),
        ("Imna ang tubig .", ["VERB", "DET", "NOUN", "PUNCT"], ["inom", "ang", "tubig", "."]),
        ("Wad-a ang basura .", ["VERB", "DET", "NOUN", "PUNCT"], ["wala", "ang", "basura", "."]),
        ("Tawga ang babaye .", ["VERB", "DET", "NOUN", "PUNCT"], ["tawag", "ang", "babaye", "."]),
        ("Gikalimtan ang balay .", ["VERB", "DET", "NOUN", "PUNCT"], ["limot", "ang", "balay", "."]),
        ("Manguha ug bato .", ["VERB", "DET", "NOUN", "PUNCT"], ["kuha", "ug", "bato", "."]),
        ("Sudlan ang balay .", ["VERB", "DET", "NOUN", "PUNCT"], ["sulod", "ang", "balay", "."]),
        ("Butangi ug asin .", ["VERB", "DET", "NOUN", "PUNCT"], ["butang", "ug", "asin", "."]),
        ("Ayaw dad-a .", ["ADV", "VERB", "PUNCT"], ["ayaw", "dala", "."]),
        ("Pangutan-a siya .", ["VERB", "PRON", "PUNCT"], ["kutana", "siya", "."]),
        ("Ganina lang .", ["ADV", "PART", "PUNCT"], ["unian", "lang", "."]),
        ("Manan-aw ta .", ["VERB", "PRON", "PUNCT"], ["tan-aw", "ta", "."]),
        ("Wala siya .", ["PART", "PRON", "PUNCT"], ["wala", "siya", "."]),
        ("Kan-a ang manukmanuk .", ["VERB", "DET", "NOUN", "PUNCT"], ["kaon", "ang", "manok", "."]),
        ("Agik-ik ang bata .", ["VERB", "DET", "NOUN", "PUNCT"], ["agik-ik", "ang", "bata", "."]),
    ],
    "HILIGAYNON": [
        ("Kan-a ang tinapay .", ["VERB", "DET", "NOUN", "PUNCT"], ["kaon", "ang", "tinapay", "."]),
        ("Dal-a ang bata .", ["VERB", "DET", "NOUN", "PUNCT"], ["dala", "ang", "bata", "."]),
        ("Imna ang tubig .", ["VERB", "DET", "NOUN", "PUNCT"], ["inom", "ang", "tubig", "."]),
        ("Sudla ang balay .", ["VERB", "DET", "NOUN", "PUNCT"], ["sulod", "ang", "balay", "."]),
        ("Wad-a ang sala .", ["VERB", "DET", "NOUN", "PUNCT"], ["wala", "ang", "sala", "."]),
        ("Tun-an ang leksyon .", ["VERB", "DET", "NOUN", "PUNCT"], ["tuon", "ang", "leksyon", "."]),
        ("Patyon ang suga .", ["VERB", "DET", "NOUN", "PUNCT"], ["patay", "ang", "suga", "."]),
        ("Taw-an mo .", ["VERB", "PRON", "PUNCT"], ["hatag", "imo", "."]),
        ("Kuh-an sang bato .", ["VERB", "ADP", "NOUN", "PUNCT"], ["kuha", "sang", "bato", "."]),
        ("Lut-on ang pagkaon .", ["VERB", "DET", "NOUN", "PUNCT"], ["luto", "ang", "pagkaon", "."]),
        ("Kalipay namon .", ["NOUN", "PRON", "PUNCT"], ["kalipay", "namon", "."]),
        ("Kalisud gid .", ["NOUN", "PART", "PUNCT"], ["lisud", "gid", "."]),
        ("Maayo ang uloulo .", ["ADJ", "DET", "ADJ", "PUNCT"], ["maayo", "ang", "uloulo", "."]),
        ("Yawyaw ang bata .", ["VERB", "DET", "NOUN", "PUNCT"], ["yawyaw", "ang", "bata", "."]),
        ("Kuskos sang salog .", ["VERB", "ADP", "NOUN", "PUNCT"], ["kuskos", "sang", "salog", "."]),
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. GENERATE PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────
results = []
print("\n🚀 Running Lemma Predictions...")

for dialect, test_cases in TEST_DATA.items():
    print(f"Processing {dialect}...")
    for sentence, expected_tags, expected_lemmas in test_cases:
        tokens = sentence.split()
        
        # 1. Affix-Based Pipeline
        try:
            affix_pos = predict_pos_batch(tokens, dialect)
            affix_lemma = [smart_lemmatize(t, p, dialect) for t, p in zip(tokens, affix_pos)]
        except:
            affix_lemma = ["ERR"] * len(tokens)

        # 2. CRF-Based Pipeline
        try:
            feats = format_tokens_for_crf(tokens)
            crf_pos = predict_pos(feats, dialect)
            crf_lemma = [smart_lemmatize(t, p, dialect) for t, p in zip(tokens, crf_pos)]
        except:
            crf_lemma = ["ERR"] * len(tokens)

        for i in range(len(tokens)):
            results.append({
                "Actual_Lemma": expected_lemmas[i],
                "Affix_Lemma": affix_lemma[i],
                "CRF_Lemma": crf_lemma[i]
            })

df = pd.DataFrame(results)

# ─────────────────────────────────────────────────────────────────────────────
# 5. PLOT SEPARATE CONFUSION MATRICES (LEMMA)
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Generating Lemma Confusion Matrices...")

# Filter errors
clean_df = df[(df['Affix_Lemma'] != 'ERR') & (df['CRF_Lemma'] != 'ERR')]

# Collect all unique lemmas involved to form the matrix axes
all_lemmas = sorted(list(set(clean_df['Actual_Lemma'].unique()) | 
                         set(clean_df['Affix_Lemma'].unique()) | 
                         set(clean_df['CRF_Lemma'].unique())))

# Matrix 1: Affix-Based
cm_affix = confusion_matrix(clean_df['Actual_Lemma'], clean_df['Affix_Lemma'], labels=all_lemmas)

plt.figure(figsize=(24, 20)) # Large size for readability
sns.heatmap(cm_affix, annot=False, cmap='Reds', xticklabels=all_lemmas, yticklabels=all_lemmas, cbar=True)
plt.title('Rule-Based (Affix) Lemma Confusion Matrix', fontsize=20, fontweight='bold', pad=20)
plt.xlabel('Predicted Lemma', fontsize=14)
plt.ylabel('Actual Lemma', fontsize=14)
plt.xticks(rotation=90, fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
path_affix = OUTPUT_DIR / "lemma_matrix_affix.png"
plt.savefig(path_affix, dpi=300)
plt.close()
print(f"✅ Saved Affix Lemma Matrix to: {path_affix}")

# Matrix 2: CRF-Based
cm_crf = confusion_matrix(clean_df['Actual_Lemma'], clean_df['CRF_Lemma'], labels=all_lemmas)

plt.figure(figsize=(24, 20)) # Large size for readability
sns.heatmap(cm_crf, annot=False, cmap='Greens', xticklabels=all_lemmas, yticklabels=all_lemmas, cbar=True)
plt.title('Hybrid (CRF) Lemma Confusion Matrix', fontsize=20, fontweight='bold', pad=20)
plt.xlabel('Predicted Lemma', fontsize=14)
plt.ylabel('Actual Lemma', fontsize=14)
plt.xticks(rotation=90, fontsize=8)
plt.yticks(fontsize=8)
plt.tight_layout()
path_crf = OUTPUT_DIR / "lemma_matrix_crf.png"
plt.savefig(path_crf, dpi=300)
plt.close()
print(f"✅ Saved CRF Lemma Matrix to:   {path_crf}")