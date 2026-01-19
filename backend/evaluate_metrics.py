import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
import sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP & IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
# Add the current directory to sys.path to ensure we can import 'core'
sys.path.append(str(Path(__file__).resolve().parent))

try:
    # Importing YOUR actual functions based on the code you provided
    from core.tagger.affix_tagging import predict_pos_batch
    from core.tagger.crf_tagging import predict_pos, format_tokens_for_crf
    print("✅ Successfully imported backend taggers.")
except ImportError as e:
    print(f"❌ Error importing taggers: {e}")
    print("   Ensure this script is in the root directory (parent of 'core').")
    sys.exit(1)

warnings.filterwarnings('ignore')  # Clean up output

# ─────────────────────────────────────────────────────────────────────────────
# 2. GROUND TRUTH TEST DATA (The Gold Standard)
# ─────────────────────────────────────────────────────────────────────────────
# Format: "Dialect": [ ("Sentence String", ["TAG", "TAG", ...]) ]

TEST_DATA = {
    "ILOCANO": [
        ("Nangan ni Juan", ["VERB", "DET", "NOUN"]),
        ("Napintas ti balasang", ["ADJ", "DET", "NOUN"]),
        ("Agsursurat ti ubing", ["VERB", "DET", "NOUN"]),
        ("Naimbag nga bigat", ["ADJ", "PART", "NOUN"]),
        ("Gumatang isuna ti sapatos", ["VERB", "PRON", "DET", "NOUN"]),
        ("Agtrabaho ni manang", ["VERB", "DET", "NOUN"]),
    ],
    "CEBUANO": [
        ("Nikaon ang bata", ["VERB", "DET", "NOUN"]),
        ("Gwapa ang babaye", ["ADJ", "DET", "NOUN"]),
        ("Nagpalit si Maria", ["VERB", "DET", "NOUN"]),
        ("Gikapoy na ko", ["VERB", "ADV", "PRON"]),
        ("Mokaon ang bata og tinapay", ["VERB", "DET", "NOUN", "PART", "NOUN"]),
        ("Gibuhat kini sa panday", ["VERB", "PRON", "ADP", "NOUN"]),
    ],
    "HILIGAYNON": [
        ("Nagdalagan ang ido", ["VERB", "DET", "NOUN"]),
        ("Maanyag ang dalaga", ["ADJ", "DET", "NOUN"]),
        ("Nagakaon sila", ["VERB", "PRON"]),
        ("Manugbulong siya", ["NOUN", "PRON"]),
        ("Ginaluto niya ang isda", ["VERB", "PRON", "DET", "NOUN"]),
        ("Guapa ang babaye", ["ADJ", "DET", "NOUN"]),
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. EVALUATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
results = []

print("\n🚀 Starting Evaluation Pipeline...\n")

for dialect, test_cases in TEST_DATA.items():
    print(f"Processing {dialect}...")
    
    for sentence, expected_tags in test_cases:
        tokens = sentence.split()
        
        # --- A. Get Affix Predictions ---
        # Your affix_tagging.py uses predict_pos_batch(tokens, dialect)
        try:
            pred_affix = predict_pos_batch(tokens, dialect)
        except Exception as e:
            # Fallback if dictionary lookup fails (e.g. file not found)
            pred_affix = ["ERR"] * len(tokens)
            print(f"  ⚠️ Affix Error on '{sentence}': {e}")

        # --- B. Get CRF Predictions ---
        # Your crf_tagging.py uses format_tokens_for_crf(tokens) -> predict_pos(features, dialect)
        try:
            features = format_tokens_for_crf(tokens)
            pred_crf = predict_pos(features, dialect)
        except Exception as e:
            pred_crf = ["ERR"] * len(tokens)
            print(f"  ⚠️ CRF Error on '{sentence}': {e}")

        # --- C. Store Results Word-by-Word ---
        # Truncate to shortest length to prevent index errors if models hallucinate tokens
        min_len = min(len(expected_tags), len(pred_affix), len(pred_crf))
        
        for i in range(min_len):
            results.append({
                "Dialect": dialect,
                "Word": tokens[i],
                "Actual": expected_tags[i],
                "Affix_Pred": pred_affix[i],
                "CRF_Pred": pred_crf[i]
            })

# Create DataFrame
df = pd.DataFrame(results)

# ─────────────────────────────────────────────────────────────────────────────
# 4. METRICS CALCULATION
# ─────────────────────────────────────────────────────────────────────────────

def get_metrics_summary(df_subset, pred_col, model_name):
    y_true = df_subset['Actual']
    y_pred = df_subset[pred_col]
    
    # Calculate weighted metrics
    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    acc = accuracy_score(y_true, y_pred)
    
    return {
        "Dialect": df_subset['Dialect'].iloc[0],
        "Model": model_name,
        "Accuracy": acc,
        "Precision": report['weighted avg']['precision'],
        "Recall": report['weighted avg']['recall'],
        "F1-Score": report['weighted avg']['f1-score']
    }

metrics_list = []

# Calculate per dialect
for dialect in df['Dialect'].unique():
    subset = df[df['Dialect'] == dialect]
    metrics_list.append(get_metrics_summary(subset, 'Affix_Pred', 'Affix-Based'))
    metrics_list.append(get_metrics_summary(subset, 'CRF_Pred', 'CRF-Based'))

# Calculate Overall
metrics_list.append({
    "Dialect": "OVERALL",
    "Model": "Affix-Based",
    "Accuracy": accuracy_score(df['Actual'], df['Affix_Pred']),
    "Precision": classification_report(df['Actual'], df['Affix_Pred'], output_dict=True, zero_division=0)['weighted avg']['precision'],
    "Recall": classification_report(df['Actual'], df['Affix_Pred'], output_dict=True, zero_division=0)['weighted avg']['recall'],
    "F1-Score": classification_report(df['Actual'], df['Affix_Pred'], output_dict=True, zero_division=0)['weighted avg']['f1-score']
})
metrics_list.append({
    "Dialect": "OVERALL",
    "Model": "CRF-Based",
    "Accuracy": accuracy_score(df['Actual'], df['CRF_Pred']),
    "Precision": classification_report(df['Actual'], df['CRF_Pred'], output_dict=True, zero_division=0)['weighted avg']['precision'],
    "Recall": classification_report(df['Actual'], df['CRF_Pred'], output_dict=True, zero_division=0)['weighted avg']['recall'],
    "F1-Score": classification_report(df['Actual'], df['CRF_Pred'], output_dict=True, zero_division=0)['weighted avg']['f1-score']
})

metrics_df = pd.DataFrame(metrics_list)

print("\n=== 📊 EVALUATION METRICS SUMMARY ===")
# Display sorted by Dialect for readability
print(metrics_df.sort_values(by=["Dialect", "Model"]).to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 5. VISUALIZATION & SAVING
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenering Plots...")

# Create 'results' folder if it doesn't exist
output_dir = Path("results")
output_dir.mkdir(exist_ok=True)

# A. Bar Chart Comparison
plt.figure(figsize=(12, 6))
sns.set_style("whitegrid")

# Filter data for plotting
plot_data = metrics_df[metrics_df["Dialect"] != "OVERALL"]
plot_data = plot_data.melt(id_vars=["Dialect", "Model"], 
                           value_vars=["Accuracy", "F1-Score"], 
                           var_name="Metric", value_name="Score")

ax = sns.barplot(data=plot_data, x="Dialect", y="Score", hue="Model", palette=["#e74c3c", "#2ecc71"])
plt.title("Performance Comparison: Affix-Based vs. CRF-Based", fontsize=14, fontweight='bold')
plt.ylim(0, 1.15)
plt.legend(loc='lower right')

for container in ax.containers:
    ax.bar_label(container, fmt='%.2f', padding=3)

plt.tight_layout()

# SAVE BAR CHART
chart_path = output_dir / "results_bar_chart.png"
plt.savefig(chart_path, dpi=300)
print(f"✅ Saved Bar Chart to: {chart_path}")
plt.close() # Close plot to free memory


# B. Confusion Matrices
clean_df = df[(df['Affix_Pred'] != 'ERR') & (df['CRF_Pred'] != 'ERR')]
labels = sorted(clean_df['Actual'].unique())

fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Affix Matrix
cm_affix = confusion_matrix(clean_df['Actual'], clean_df['Affix_Pred'], labels=labels)
sns.heatmap(cm_affix, annot=True, fmt='d', cmap='Reds', xticklabels=labels, yticklabels=labels, ax=axes[0])
axes[0].set_title("Affix-Based Confusion Matrix")
axes[0].set_xlabel("Predicted")
axes[0].set_ylabel("Actual")

# CRF Matrix
cm_crf = confusion_matrix(clean_df['Actual'], clean_df['CRF_Pred'], labels=labels)
sns.heatmap(cm_crf, annot=True, fmt='d', cmap='Greens', xticklabels=labels, yticklabels=labels, ax=axes[1])
axes[1].set_title("CRF-Based Confusion Matrix")
axes[1].set_xlabel("Predicted")
axes[1].set_ylabel("Actual")

plt.tight_layout()

# SAVE MATRIX IMAGE
matrix_path = output_dir / "results_confusion_matrix.png"
plt.savefig(matrix_path, dpi=300)
print(f"✅ Saved Confusion Matrix to: {matrix_path}")
plt.close()