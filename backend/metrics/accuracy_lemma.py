import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP
# ─────────────────────────────────────────────────────────────────────────────
BACKEND_DIR = Path(__file__).resolve().parent
os.chdir(BACKEND_DIR)
OUTPUT_DIR = BACKEND_DIR / "results"
OUTPUT_DIR.mkdir(exist_ok=True)

print(f"📂 Saving Chart to: {OUTPUT_DIR}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA (From your Test Results)
# ─────────────────────────────────────────────────────────────────────────────
data = {
    "Model": ["Rule-Based (Affix)", "Hybrid (CRF)"],
    "Accuracy": [0.67, 1.00]  # 0.666667 rounded to 0.67
}

df = pd.DataFrame(data)

# ─────────────────────────────────────────────────────────────────────────────
# 3. PLOT CHART
# ─────────────────────────────────────────────────────────────────────────────
plt.figure(figsize=(8, 6))
sns.set_style("whitegrid")

# Color Palette: Muted Red for "Fail" (Affix), Bright Green for "Perfect" (CRF)
colors = ["#e74c3c", "#2ecc71"] 

ax = sns.barplot(
    data=df, 
    x="Model", 
    y="Accuracy", 
    palette=colors,
    edgecolor="0.2"
)

# Styling
plt.title("Accuracy on Ambiguous Words ('Trap' Cases)", fontsize=15, fontweight='bold', pad=20)
plt.ylabel("Accuracy Score", fontsize=12)
plt.xlabel("Pipeline Type", fontsize=12)
plt.ylim(0, 1.15) 

# Add Labels (0.67 vs 1.00)
for i, container in enumerate(ax.containers):
    ax.bar_label(container, fmt='%.2f', padding=5, fontsize=13, fontweight='bold')

# Save
save_path = OUTPUT_DIR / "ambiguity_accuracy_chart.png"
plt.tight_layout()
plt.savefig(save_path, dpi=300)
print(f"✅ Chart Generated: {save_path}")
plt.close()