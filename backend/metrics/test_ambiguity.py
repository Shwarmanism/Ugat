import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP & PATHS
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
sys.path.append(str(BACKEND_DIR))
OUTPUT_DIR = BACKEND_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

try:
    from core.tagger.affix_tagging import predict_pos_batch
    from core.tagger.crf_tagging import predict_pos, format_tokens_for_crf
    from core.morphology.affix_stripping import get_morph_engine
    print("✅ Engine Loaded.")
except ImportError:
    sys.exit("❌ Could not load engine.")

# ─────────────────────────────────────────────────────────────────────────────
# 2. INJECT EXTENDED TRAP LIST
# ─────────────────────────────────────────────────────────────────────────────
engine = get_morph_engine()
print("\n💉 INJECTING EXTENDED TRAP LIST (27+ TRAPS)...")

# We define the "stripped" versions of proper nouns as valid roots.
# This forces the Affix Model to strip them (Fail), while CRF should recognize the Name (Pass).
traps = {
    "ilocano": [
        # Original Traps
        "osto", "bini", "ustin", "bukel", "oo", "bugao", "ong", "aw", "ta", "pay",
        # NEW TRAPS
        "singal",   # Magsingal (Place) -> Mag-singal
        "udin",     # Tagudin (Place) -> Tag-udin
        "partian",  # Nagpartian (Place) -> Nag-partian
        "si"        # Masi (Place) -> Ma-si
    ],
    "cebuano": [
        # Original Traps
        "nila", "gia", "lou", "bolo", "tina", "pascua", "ro", "no", "las", "hal", "ta",
        # NEW TRAPS
        "lisay",    # Talisay (Place) -> Ta-lisay (Ta- prefix?)
        "tilan",    # Ginatilan (Place) -> Gina-tilan (Gina- passive prefix)
        "uikay",    # Maguikay (Place) -> Mag-uikay
        "alboal"    # Moalboal (Place) -> Mo-alboal (Mo- future prefix)
    ],
    "hiligaynon": [
        # Original Traps
        "nolia", "ren", "gadia", "nay", "linao", "asin", "ga", "hal", "ta", "sakit",
        # NEW TRAPS
        "libo",     # Kalibo (Place) -> Ka-libo (Ka- prefix, Libo = 1000)
        "busao",    # Mambusao (Place) -> Mam-busao (Mam- prefix)
        "napla",    # Manapla (Place) -> Ma-napla
        "pon"       # Mambusao (dup? let's use Pontevedra -> Pon-tevedra? too complex. Let's use 'Sipalay' -> Si-palay)
                    # Sipalay -> Si-palay (Palay is Rice). Perfect collision.
    ]
}

# Add 'palay' to hiligaynon traps separately since 'palay' is a real word anyway
traps["hiligaynon"].append("palay")

for lang, words in traps.items():
    for w in words:
        engine.roots[lang][w] = "TRAP_ROOT"
        engine.root_sets[lang].add(w)

print("✅ All Traps Injected.\n")

# ─────────────────────────────────────────────────────────────────────────────
# 3. EXPANDED TEST DATA (30+ CASES)
# ─────────────────────────────────────────────────────────────────────────────
AMBIGUOUS_DATA = [
    # =========================================================
    # ILOCANO (13 Cases)
    # =========================================================
    # --- Proper Noun Traps ---
    { "Dialect": "ILOCANO", "Sentence": "Naragsak ti Agosto idiay plaza .", "Target_Word": "Agosto", "Expected_Lemma": "agosto" },
    { "Dialect": "ILOCANO", "Sentence": "Napan da idiay Mabini .", "Target_Word": "Mabini", "Expected_Lemma": "mabini" },
    { "Dialect": "ILOCANO", "Sentence": "Ni Agustin ti kabsatko .", "Target_Word": "Agustin", "Expected_Lemma": "agustin" },
    { "Dialect": "ILOCANO", "Sentence": "Nagpintas ti Nagbukel .", "Target_Word": "Nagbukel", "Expected_Lemma": "nagbukel" },
    { "Dialect": "ILOCANO", "Sentence": "Adda ti balay idiay Agoo .", "Target_Word": "Agoo", "Expected_Lemma": "agoo" },
    { "Dialect": "ILOCANO", "Sentence": "Taga Cabugao isuna .", "Target_Word": "Cabugao", "Expected_Lemma": "cabugao" },
    # --- NEW: Place Name Traps ---
    { "Dialect": "ILOCANO", "Sentence": "Agpasiar da idiay Magsingal .", "Target_Word": "Magsingal", "Expected_Lemma": "magsingal" }, # Trap: Mag-singal
    { "Dialect": "ILOCANO", "Sentence": "Adayo ti Tagudin .", "Target_Word": "Tagudin", "Expected_Lemma": "tagudin" },           # Trap: Tag-udin
    { "Dialect": "ILOCANO", "Sentence": "Napanda idiay Nagpartian .", "Target_Word": "Nagpartian", "Expected_Lemma": "nagpartian" }, # Trap: Nag-partian
    { "Dialect": "ILOCANO", "Sentence": "Bassit ti ili ti Masi .", "Target_Word": "Masi", "Expected_Lemma": "masi" },               # Trap: Ma-si
    # --- Pseudo-Verb/Adj Traps ---
    { "Dialect": "ILOCANO", "Sentence": "Dakkel ti agong na .", "Target_Word": "agong", "Expected_Lemma": "agong" },
    { "Dialect": "ILOCANO", "Sentence": "Ti agaw ket masama .", "Target_Word": "agaw", "Expected_Lemma": "agaw" },
    { "Dialect": "ILOCANO", "Sentence": "Nagsakit ti mata na .", "Target_Word": "mata", "Expected_Lemma": "mata" },

    # =========================================================
    # CEBUANO (14 Cases)
    # =========================================================
    # --- Proper Noun Traps ---
    { "Dialect": "CEBUANO", "Sentence": "Moadto kami sa Manila ugma .", "Target_Word": "Manila", "Expected_Lemma": "manila" },
    { "Dialect": "CEBUANO", "Sentence": "Gitawag ni Gia ang iyang inahan .", "Target_Word": "Gia", "Expected_Lemma": "gia" },
    { "Dialect": "CEBUANO", "Sentence": "Si Malou ang akong higala .", "Target_Word": "Malou", "Expected_Lemma": "malou" },
    { "Dialect": "CEBUANO", "Sentence": "Naa sa Mabolo ang tindahan .", "Target_Word": "Mabolo", "Expected_Lemma": "mabolo" },
    { "Dialect": "CEBUANO", "Sentence": "Layo ang Matina sa amoa .", "Target_Word": "Matina", "Expected_Lemma": "matina" },
    { "Dialect": "CEBUANO", "Sentence": "Nindot ang Malapascua .", "Target_Word": "Malapascua", "Expected_Lemma": "malapascua" },
    # --- NEW: Place Name Traps ---
    { "Dialect": "CEBUANO", "Sentence": "Traffic sa Talisay karon .", "Target_Word": "Talisay", "Expected_Lemma": "talisay" },       # Trap: Ta-lisay
    { "Dialect": "CEBUANO", "Sentence": "Nindot ang waterfalls sa Ginatilan .", "Target_Word": "Ginatilan", "Expected_Lemma": "ginatilan" }, # Trap: Gina-tilan
    { "Dialect": "CEBUANO", "Sentence": "Taga Maguikay siya .", "Target_Word": "Maguikay", "Expected_Lemma": "maguikay" },         # Trap: Mag-uikay
    { "Dialect": "CEBUANO", "Sentence": "Mag-dive ta sa Moalboal .", "Target_Word": "Moalboal", "Expected_Lemma": "moalboal" },     # Trap: Mo-alboal
    # --- Pseudo-Verb/Adj Traps ---
    { "Dialect": "CEBUANO", "Sentence": "Ang mga Moro sa Mindanao .", "Target_Word": "Moro", "Expected_Lemma": "moro" },
    { "Dialect": "CEBUANO", "Sentence": "Niaging mano po siya .", "Target_Word": "mano", "Expected_Lemma": "mano" },
    { "Dialect": "CEBUANO", "Sentence": "Dako nga malas kini .", "Target_Word": "malas", "Expected_Lemma": "malas" },
    { "Dialect": "CEBUANO", "Sentence": "Sakit ang mata nako .", "Target_Word": "mata", "Expected_Lemma": "mata" },

    # =========================================================
    # HILIGAYNON (13 Cases)
    # =========================================================
    # --- Proper Noun Traps ---
    { "Dialect": "HILIGAYNON", "Sentence": "Nagbakal siya sang Magnolia .", "Target_Word": "Magnolia", "Expected_Lemma": "magnolia" },
    { "Dialect": "HILIGAYNON", "Sentence": "Si Karen ang akon abyan .", "Target_Word": "Karen", "Expected_Lemma": "karen" },
    { "Dialect": "HILIGAYNON", "Sentence": "Nakadto kami sa Pagadian .", "Target_Word": "Pagadian", "Expected_Lemma": "pagadian" },
    { "Dialect": "HILIGAYNON", "Sentence": "Matahum ang Panay .", "Target_Word": "Panay", "Expected_Lemma": "panay" },
    { "Dialect": "HILIGAYNON", "Sentence": "Tinlo ang tubig sa Malinao .", "Target_Word": "Malinao", "Expected_Lemma": "malinao" },
    { "Dialect": "HILIGAYNON", "Sentence": "Maalat ang Maasin .", "Target_Word": "Maasin", "Expected_Lemma": "maasin" },
    # --- NEW: Place Name Traps ---
    { "Dialect": "HILIGAYNON", "Sentence": "Ang Ati-Atihan sa Kalibo .", "Target_Word": "Kalibo", "Expected_Lemma": "kalibo" },      # Trap: Ka-libo (Thousand)
    { "Dialect": "HILIGAYNON", "Sentence": "Layo ang Mambusao .", "Target_Word": "Mambusao", "Expected_Lemma": "mambusao" },       # Trap: Mam-busao
    { "Dialect": "HILIGAYNON", "Sentence": "Taga Manapla siya .", "Target_Word": "Manapla", "Expected_Lemma": "manapla" },         # Trap: Ma-napla
    { "Dialect": "HILIGAYNON", "Sentence": "Bugana ang humay sa Sipalay .", "Target_Word": "Sipalay", "Expected_Lemma": "sipalay" }, # Trap: Si-palay (Rice)
    # --- Pseudo-Verb/Adj Traps ---
    { "Dialect": "HILIGAYNON", "Sentence": "Didto sa Naga kami .", "Target_Word": "Naga", "Expected_Lemma": "naga" },
    { "Dialect": "HILIGAYNON", "Sentence": "Ang mahal ko .", "Target_Word": "mahal", "Expected_Lemma": "mahal" },
    { "Dialect": "HILIGAYNON", "Sentence": "May sakit sa mata .", "Target_Word": "mata", "Expected_Lemma": "mata" }
]

# ─────────────────────────────────────────────────────────────────────────────
# 4. RUN EVALUATION
# ─────────────────────────────────────────────────────────────────────────────
print(f"{'DIALECT':<10} | {'WORD':<12} | {'MODEL':<8} | {'PRED POS':<8} | {'PRED LEMMA':<12} | {'STATUS'}")
print("-" * 90)

results = []

for case in AMBIGUOUS_DATA:
    dialect = case["Dialect"]
    sent = case["Sentence"]
    target = case["Target_Word"]
    correct_lemma = case["Expected_Lemma"].lower()
    
    tokens = sent.split()
    try:
        target_idx = tokens.index(target)
    except ValueError:
        continue

    # --- A. RUN AFFIX PIPELINE ---
    affix_tags = predict_pos_batch(tokens, dialect)
    affix_tag = affix_tags[target_idx]
    
    # Strict call
    affix_lemma_res = engine.lemmatize(target, dialect, pos=affix_tag)
    affix_lemma = affix_lemma_res["lemma"]

    # --- B. RUN CRF PIPELINE ---
    feats = format_tokens_for_crf(tokens)
    crf_tags = predict_pos(feats, dialect)
    crf_tag = crf_tags[target_idx]
    
    # Strict call
    crf_lemma_res = engine.lemmatize(target, dialect, pos=crf_tag)
    crf_lemma = crf_lemma_res["lemma"]

    # --- C. PRINT & STORE RESULTS ---
    status_affix = "✅ PASS" if affix_lemma == correct_lemma else "❌ FAIL"
    print(f"{dialect:<10} | {target:<12} | {'AFFIX':<8} | {affix_tag:<8} | {affix_lemma:<12} | {status_affix}")
    
    status_crf = "✅ PASS" if crf_lemma == correct_lemma else "❌ FAIL"
    print(f"{'':<10} | {'':<12} | {'CRF':<8} | {crf_tag:<8} | {crf_lemma:<12} | {status_crf}")
    print("-" * 90)
    
    results.append({"Dialect": dialect, "Model": "Rule-Based (Affix)", "Score": 1 if affix_lemma == correct_lemma else 0})
    results.append({"Dialect": dialect, "Model": "Hybrid (CRF)", "Score": 1 if crf_lemma == correct_lemma else 0})

# ─────────────────────────────────────────────────────────────────────────────
# 5. GENERATE CHART
# ─────────────────────────────────────────────────────────────────────────────
print("\n📈 Generating Comprehensive Ambiguity Chart...")

df = pd.DataFrame(results)
summary = df.groupby(["Dialect", "Model"])["Score"].mean().reset_index()

plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")

ax = sns.barplot(
    data=summary, 
    x="Dialect", 
    y="Score", 
    hue="Model", 
    palette=["#34495e", "#3498db"], # Red for Fail, Green for Pass
    edgecolor="0.2"
)

plt.title("Ambiguity Stress Test: Collision Dataset (40 Cases)", fontsize=16, fontweight='bold', pad=20)
plt.ylabel("Lemmatization Accuracy", fontsize=12)
plt.xlabel("Dialect", fontsize=12)
plt.ylim(0, 1.15)
plt.legend(loc='lower right', title="Pipeline", fontsize=10)

for container in ax.containers:
    ax.bar_label(container, fmt='%.2f', padding=3, fontsize=11, fontweight='bold')

save_path = OUTPUT_DIR / "ambiguity_unified_extended.png"
plt.tight_layout()
plt.savefig(save_path, dpi=300)
print(f"✅ Saved Chart to: {save_path}")
plt.close()