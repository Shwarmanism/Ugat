import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import json
from pathlib import Path
from collections import Counter

# ─────────────────────────────────────────────────────────────────────────────
# 1. SETUP
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# Paths to your JSON Root Dictionaries
# Adjust filenames if yours are slightly different (e.g. capitalized)
DICT_FILES = {
    "ILOCANO": BASE_DIR / "resources/root_ilocano.json",
    "CEBUANO": BASE_DIR / "resources/root_cebuano.json",
    "HILIGAYNON": BASE_DIR / "resources/root_hiligaynon.json"
}

OUTPUT_DIR = BASE_DIR / "results/charts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────────────────────────────────────
# 2. DATA LOADER (Reads JSON Keys & Values)
# ─────────────────────────────────────────────────────────────────────────────
def load_and_count_dict_pos(file_path):
    if not file_path.exists():
        print(f"⚠️  Warning: File not found: {file_path}")
        return None

    pos_tags = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # The JSON format is likely: { "word": "POS", "word2": "POS" }
            # We just want to count the VALUES (the POS tags)
            for word, pos in data.items():
                # Normalize tags (e.g., "noun" -> "NOUN")
                clean_pos = pos.upper().strip()
                pos_tags.append(clean_pos)
                
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON in {file_path}")
        return None
        
    return pos_tags

# ─────────────────────────────────────────────────────────────────────────────
# 3. VISUALIZATION
# ─────────────────────────────────────────────────────────────────────────────
def plot_dict_distribution(dialect, tags):
    counts = Counter(tags)
    total = sum(counts.values())
    
    # Create DataFrame
    df = pd.DataFrame.from_dict(counts, orient='index', columns=['Count']).reset_index()
    df = df.rename(columns={'index': 'POS'})
    
    # Calculate Percentage
    df['Percentage'] = (df['Count'] / total) * 100
    
    # Sort for cleaner look
    df = df.sort_values(by='Percentage', ascending=False)

    # Setup Plot
    plt.figure(figsize=(10, 6))
    sns.set_style("whitegrid")
    
    # Use 'Magma' palette for a distinct look from your Corpus charts
    ax = sns.barplot(
        data=df, 
        x="Percentage", 
        y="POS", 
        palette="magma",
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
            fontsize=10, 
            fontweight='bold',
            color='#333'
        )

    plt.title(f"Root Dictionary Composition: {dialect.upper()}", fontsize=14, fontweight='bold', pad=15)
    plt.xlabel("Percentage of Dictionary Entries (%)", fontsize=11)
    plt.ylabel("Root Category", fontsize=11)
    
    if not df.empty:
        plt.xlim(0, df['Percentage'].max() + 15)
    
    save_path = OUTPUT_DIR / f"dict_distribution_{dialect.lower()}.png"
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved chart to: {save_path}")
    plt.close()

# ─────────────────────────────────────────────────────────────────────────────
# 4. MAIN EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"📂 Script Location: {BASE_DIR}")
    print("📖 Analyzing Root Dictionaries...\n")
    
    for dialect, path in DICT_FILES.items():
        print(f"Processing {dialect} Dictionary...")
        tags = load_and_count_dict_pos(path)
        
        if tags:
            print(f"   Found {len(tags)} entries.")
            plot_dict_distribution(dialect, tags)
        else:
            print(f"   ❌ Skipping {dialect} (File missing or empty)")
            
    print(f"\n✨ Done! Check the folder: {OUTPUT_DIR}")