import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from pathlib import Path
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

DATASETS = {
    "ILOCANO": BASE_DIR / "resources/ilocano_crf_formatted.txt",
    "CEBUANO": BASE_DIR / "resources/Cebuano_crf_formatted.txt",
    "HILIGAYNON": BASE_DIR / "resources/Hiligaynon_crf_formatted.txt"
}

OUTPUT_DIR = BASE_DIR / "results/charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADER
# ─────────────────────────────────────────────────────────────────────────────
def load_and_count_tags(file_path):
    if not file_path.exists():
        print(f"⚠️  Warning: File not found: {file_path}")
        return None

    tags = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2: 
                tags.append(parts[-1])
    return tags

# ─────────────────────────────────────────────────────────────────────────────
# 3. VISUALIZATION (With Threshold Filter)
# ─────────────────────────────────────────────────────────────────────────────
def plot_distribution(dialect, tags):
    counts = Counter(tags)
    total = sum(counts.values())
    
    df = pd.DataFrame.from_dict(counts, orient='index', columns=['Count']).reset_index()
    df = df.rename(columns={'index': 'POS'})
    df['Percentage'] = (df['Count'] / total) * 100
    
    # --- ✂️ FILTERING STEP ✂️ ---
    # Remove anything less than 1.0%
    df_filtered = df[df['Percentage'] >= 1.0].copy()
    
    # Sort by Percentage
    df_filtered = df_filtered.sort_values(by='Percentage', ascending=False)

    # Setup Plot
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    ax = sns.barplot(
        data=df_filtered, 
        x="Percentage", 
        y="POS", 
        palette="GnBu_r",
        edgecolor="0.2"
    )

    # Add labels
    for i, p in enumerate(ax.patches):
        width = p.get_width()
        plt.text(
            width + 0.5,
            p.get_y() + p.get_height()/2 + 0.1,
            f'{width:.2f}%',
            ha="left", 
            fontsize=11, 
            fontweight='bold',
            color='#0d4f4d'
        )

    plt.title(f"POS Distribution: {dialect.upper()} (>= 1.0%)", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Percentage of Corpus (%)", fontsize=11)
    plt.ylabel("POS Tag", fontsize=11)
    
    # Adjust x-limit dynamically
    if not df_filtered.empty:
        plt.xlim(0, df_filtered['Percentage'].max() + 15)
    
    save_path = OUTPUT_DIR / f"distribution_{dialect.lower()}.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved chart to: {save_path} (Filtered < 1.0%)")
    plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# 4. MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📂 Script Location: {BASE_DIR}")
    print("📊 Generating Filtered Distribution Charts...\n")
    
    for dialect, path in DATASETS.items():
        print(f"Processing {dialect}...")
        tags = load_and_count_tags(path)
        
        if tags:
            plot_distribution(dialect, tags)
        else:
            print(f"   ❌ Skipping {dialect} (File missing)")
            
    print(f"\n✨ Done! Check the folder: {OUTPUT_DIR}")