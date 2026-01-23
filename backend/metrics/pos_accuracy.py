import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score
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
OUTPUT_DIR = BACKEND_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📂 Execution Context: {BACKEND_DIR}")

# Import Engine
try:
    from core.tagger.affix_tagging import predict_pos_batch
    from core.tagger.crf_tagging import predict_pos, format_tokens_for_crf
    print("✅ Backend Engine Loaded!")
except ImportError as e:
    print(f"❌ Import Error: {e}")
    sys.exit(1)

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────────────────────────────────────
# 2. TEST DATA (Verified Set)
# ─────────────────────────────────────────────────────────────────────────────
TEST_DATA = {
    "ILOCANO": [
        ("Napan da idiay balay .", ["VERB", "PRON", "DEM", "NOUN", "PUNCT"]),
        ("Agbuybuya dagiti ubbing iti plaza .", ["VERB", "DET", "NOUN", "ADP", "NOUN", "PUNCT"]),
        ("Agkatkatawa ti lalaki idiay balay .", ["VERB", "DET", "NOUN", "ADP", "NOUN", "PUNCT"]),
        ("Nagkatawa dagiti ub-ubbing .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Ag-agawid kami no malpas ti trabaho .", ["VERB", "PRON", "CONJ", "VERB", "DET", "NOUN", "PUNCT"]),
        ("Ginatangna ti dakkel a tinapay .", ["VERB", "DET", "ADJ", "PART", "NOUN", "PUNCT"]),
        ("Linuto da ti manok para kenkuana .", ["VERB", "PRON", "DET", "NOUN", "ADP", "PRON", "PUNCT"]),
        ("Nu agturposka , agtrabahoka idiay Manila .", ["CONJ", "VERB", "PUNCT", "VERB", "ADP", "NOUN", "PUNCT"]),
        ("Kayatko nga agbasa ti libro ngem awan ti oras .", ["VERB", "PART", "VERB", "DET", "NOUN", "CONJ", "ADV", "DET", "NOUN", "PUNCT"]),
        ("Tumatayab ti manok .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Nangus-usar da ti lapis .", ["VERB", "PRON", "DET", "NOUN", "PUNCT"]),
        ("Naggugudua da .", ["VERB", "PRON", "PUNCT"]),
    ],
    "CEBUANO": [
        ("Palita ang tinapay .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Dad-a ang bata .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Kan-a ang sud-an .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Imna ang tubig .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Wad-a ang basura .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Tawga ang babaye .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Gikalimtan ang balay .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Manguha ug bato .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Sudlan ang balay .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Butangi ug asin .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Ayaw dad-a .", ["ADV", "VERB", "PUNCT"]),
        ("Pangutan-a siya .", ["VERB", "PRON", "PUNCT"]),
        ("Ganina lang .", ["ADV", "PART", "PUNCT"]),
        ("Manan-aw ta .", ["VERB", "PRON", "PUNCT"]),
        ("Wala siya .", ["PART", "PRON", "PUNCT"]),
        ("Kan-a ang manukmanuk .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Agik-ik ang bata .", ["VERB", "DET", "NOUN", "PUNCT"]),
    ],
    "HILIGAYNON": [
        ("Kan-a ang tinapay .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Dal-a ang bata .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Imna ang tubig .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Sudla ang balay .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Wad-a ang sala .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Tun-an ang leksyon .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Patyon ang suga .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Taw-an mo .", ["VERB", "PRON", "PUNCT"]),
        ("Kuh-an sang bato .", ["VERB", "ADP", "NOUN", "PUNCT"]),
        ("Lut-on ang pagkaon .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Kalipay namon .", ["NOUN", "PRON", "PUNCT"]),
        ("Kalisud gid .", ["NOUN", "PART", "PUNCT"]),
        ("Maayo ang uloulo .", ["ADJ", "DET", "ADJ", "PUNCT"]),
        ("Yawyaw ang bata .", ["VERB", "DET", "NOUN", "PUNCT"]),
        ("Kuskos sang salog .", ["VERB", "ADP", "NOUN", "PUNCT"]),
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. GENERATE PREDICTIONS
# ─────────────────────────────────────────────────────────────────────────────
results = []
print("\n🚀 Running POS Taggers...")

for dialect, test_cases in TEST_DATA.items():
    print(f"Processing {dialect}...")
    for sentence, expected_tags in test_cases:
        tokens = sentence.split()
        
        # 1. Affix-Based
        try:
            affix_pos = predict_pos_batch(tokens, dialect)
        except:
            affix_pos = ["ERR"] * len(tokens)

        # 2. CRF-Based
        try:
            feats = format_tokens_for_crf(tokens)
            crf_pos = predict_pos(feats, dialect)
        except:
            crf_pos = ["ERR"] * len(tokens)

        for i in range(len(tokens)):
            results.append({
                "Dialect": dialect,
                "Actual": expected_tags[i],
                "Affix": affix_pos[i],
                "CRF": crf_pos[i]
            })

df = pd.DataFrame(results)

# ─────────────────────────────────────────────────────────────────────────────
# 4. PLOT ACCURACY CHART
# ─────────────────────────────────────────────────────────────────────────────
print("\n📊 Generating Accuracy Chart...")

chart_data = []
for dialect in df['Dialect'].unique():
    subset = df[df['Dialect'] == dialect]
    
    # Calculate Accuracy
    acc_affix = accuracy_score(subset['Actual'], subset['Affix'])
    acc_crf = accuracy_score(subset['Actual'], subset['CRF'])
    
    chart_data.append({"Dialect": dialect, "Model": "Rule-Based (Affix)", "Accuracy": acc_affix})
    chart_data.append({"Dialect": dialect, "Model": "Hybrid (CRF)", "Accuracy": acc_crf})

# Create Bar Plot
plt.figure(figsize=(10, 6))
sns.set_style("whitegrid")
ax = sns.barplot(
    data=pd.DataFrame(chart_data), 
    x="Dialect", 
    y="Accuracy", 
    hue="Model", 
    palette=["#34495e", "#3498db"], # Grey for Rule-Based, Green for Hybrid
    edgecolor="0.2"
)

# Styling
plt.title("POS Tagging Accuracy Comparison", fontsize=16, fontweight='bold', pad=20)
plt.ylabel("Accuracy Score", fontsize=12)
plt.xlabel("Dialect", fontsize=12)
plt.ylim(0, 1.15) # Add space for labels
plt.legend(loc='lower right', title="Model Type", fontsize=10)

# Add Score Labels on Bars
for container in ax.containers:
    ax.bar_label(container, fmt='%.2f', padding=3, fontsize=11, fontweight='bold')

plt.tight_layout()
save_path = OUTPUT_DIR / "pos_accuracy_comparison.png"
plt.savefig(save_path, dpi=300)
print(f"✅ Saved Accuracy Chart to: {save_path}")
plt.close()