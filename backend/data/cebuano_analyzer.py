import pandas as pd
import cebuano_affixes
import unicodedata
import os
# ==========================================
# 1. SETUP & LOADING
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'cebuano_roots_final.xlsx')

print(f"Loading Root Database from {DB_FILE}...")
try:
    df = pd.read_excel(DB_FILE)
    ROOT_DB = {}
    for idx, row in df.iterrows():
        # Clean keys for matching, keep original data for display
        clean_key = unicodedata.normalize('NFKD', str(row['word'])).encode('ASCII', 'ignore').decode('utf-8').lower()
        ROOT_DB[clean_key] = {
            'pos': str(row['POS']).lower(),
            # Handle missing definitions gracefully
            'def': str(row['definition']) if 'definition' in row else "No definition"
        }
    print(f"Database loaded! {len(ROOT_DB)} roots found.")
except FileNotFoundError:
    print("ERROR: Database not found. Run build_database_master.py first!")
    exit()

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def remove_accents(input_str):
    if not isinstance(input_str, str): return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def check_db(word):
    """Returns the full info dict if word exists, else None."""
    return ROOT_DB.get(word)

def handle_shifts(stem):
    """Handles u->o and r->d shifts (e.g., dakuon->dako)."""
    candidates = []
    if stem.endswith('u'): candidates.append(stem[:-1] + 'o')
    if stem.endswith('r'): candidates.append(stem[:-1] + 'd')
    
    for cand in candidates:
        info = check_db(cand)
        if info: return cand, info
    return None, None

def determine_final_pos(root_pos, affix_str):
    """Calculates Final POS based on Affix + Root."""
    affix_type = cebuano_affixes.get_affix_pos(affix_str)
    
    if affix_type == "neutral": return root_pos
    if affix_type == "v": return "v (derived)"
    if affix_type == "n": return "n (derived)"
    if affix_type == "adj": return "adj (derived)"
    
    return root_pos

# --- NASAL SUBSTITUTION LOGIC (For 'Pangitaan' -> 'Kita') ---
NASAL_MAP = {
    "pang": ["k", "t", "s"],
    "mang": ["k", "t", "s"],
    "nang": ["k", "t", "s"],
    "pam": ["p", "b"],
    "mam": ["p", "b"],
    "nam": ["p", "b"],
    "pan": ["d", "s", "t"],
    "man": ["d", "s", "t"],
    "nan": ["d", "s", "t"]
}

def check_nasal_substitution(prefix, stem):
    if prefix not in NASAL_MAP: return None, None
    
    for letter in NASAL_MAP[prefix]:
        reconstructed_word = letter + stem
        info = check_db(reconstructed_word)
        if info: return reconstructed_word, info
            
    return None, None

def check_reduplication(stem):
    """Handles 'hahakot' -> 'hakot'"""
    if len(stem) >= 5 and stem[0:2] == stem[2:4]:
        real_root = stem[2:]
        info = check_db(real_root)
        if info: return real_root, info
    return None, None

# ==========================================
# 3. THE ANALYZER ENGINE
# ==========================================
def analyze_word(raw_word):
    word = remove_accents(raw_word.lower().strip())
    candidates = []

    # --- 1. EXACT MATCH ---
    info = check_db(word)
    if info:
        return {"original": raw_word, "root": word, "root_pos": info['pos'], 
                "final_pos": info['pos'], "type": "exact", "score": 100}

    # --- 2. PREFIX STRIPPING ---
    for pre in cebuano_affixes.PREFIXES:
        if word.startswith(pre):
            stem = word[len(pre):]
            
            # A. Normal Check
            info = check_db(stem)
            if info:
                final_pos = determine_final_pos(info['pos'], pre)
                candidates.append({
                    "root": stem, "root_pos": info['pos'], "final_pos": final_pos, 
                    "type": "prefix", "score": len(stem)
                })
            
            # B. Nasal Substitution Check (pangitaan -> kita)
            nasal_root, nasal_info = check_nasal_substitution(pre, stem)
            if nasal_root:
                final_pos = determine_final_pos(nasal_info['pos'], pre)
                candidates.append({
                    "root": nasal_root, "root_pos": nasal_info['pos'], "final_pos": final_pos, 
                    "type": "prefix_nasal", "score": len(nasal_root)
                })

            # C. Reduplication Check (maghahakot -> hakot)
            redup_root, redup_info = check_reduplication(stem)
            if redup_root:
                final_pos = determine_final_pos(redup_info['pos'], pre)
                candidates.append({
                    "root": redup_root, "root_pos": redup_info['pos'], "final_pos": final_pos,
                    "type": "prefix_redup", "score": len(redup_root)
                })

    # --- 3. SUFFIX STRIPPING ---
    for suf in cebuano_affixes.SUFFIXES:
        if word.endswith(suf):
            stem = word[:-len(suf)]
            
            # A. Normal Check
            info = check_db(stem)
            if info:
                final_pos = determine_final_pos(info['pos'], suf)
                candidates.append({
                    "root": stem, "root_pos": info['pos'], "final_pos": final_pos, 
                    "type": "suffix", "score": len(stem)
                })
            
            # B. Shift Check (dakuon -> dako)
            shift_root, shift_info = handle_shifts(stem)
            if shift_root:
                final_pos = determine_final_pos(shift_info['pos'], suf)
                candidates.append({
                    "root": shift_root, "root_pos": shift_info['pos'], "final_pos": final_pos, 
                    "type": "suffix_shifted", "score": len(shift_root)
                })

    # --- 4. CIRCUMFIX STRIPPING (Both Sides) ---
    for pre in cebuano_affixes.PREFIXES:
        if word.startswith(pre):
            temp_stem = word[len(pre):]
            
            for suf in cebuano_affixes.SUFFIXES:
                if temp_stem.endswith(suf):
                    final_stem = temp_stem[:-len(suf)]
                    if len(final_stem) < 3: continue

                    # A. Normal Check
                    info = check_db(final_stem)
                    if info:
                        final_pos = determine_final_pos(info['pos'], pre)
                        candidates.append({
                            "root": final_stem, "root_pos": info['pos'], "final_pos": final_pos, 
                            "type": "circumfix", "score": len(final_stem)
                        })

                    # B. Nasal Substitution Check (pangitaan -> kita)
                    nasal_root, nasal_info = check_nasal_substitution(pre, final_stem)
                    if nasal_root:
                        final_pos = determine_final_pos(nasal_info['pos'], pre)
                        candidates.append({
                            "root": nasal_root, "root_pos": nasal_info['pos'], "final_pos": final_pos, 
                            "type": "circumfix_nasal", "score": len(nasal_root)
                        })

                    # C. Shift Check (kasulbaran -> sulbad)
                    shift_root, shift_info = handle_shifts(final_stem)
                    if shift_root:
                        final_pos = determine_final_pos(shift_info['pos'], pre)
                        candidates.append({
                            "root": shift_root, "root_pos": shift_info['pos'], "final_pos": final_pos, 
                            "type": "circumfix_shifted", "score": len(shift_root)
                        })

    # --- 5. INFIX STRIPPING ---
    for inf in cebuano_affixes.INFIXES:
        if word.find(inf) == 1:
            stem = word[0] + word[1+len(inf):]
            info = check_db(stem)
            if info:
                 candidates.append({
                     "root": stem, "root_pos": info['pos'], "final_pos": info['pos'], 
                     "type": "infix", "score": len(stem)
                 })

    # --- SELECT BEST CANDIDATE ---
    if not candidates:
        return {
            "original": raw_word, "root": "FAILED", 
            "root_pos": "-", "final_pos": "-", "type": "failed"
        }

    # Sort by Score (Length of root) descending
    best_match = sorted(candidates, key=lambda x: x['score'], reverse=True)[0]
    best_match['original'] = raw_word
    return best_match

# ==========================================
# TESTER
# ==========================================
if __name__ == "__main__":
    words = [
        "Mananambal", 
        "Nagkasabot", 
        "Pangitaan", 
        "Kasulbaran", 
        "Gihambin", 
        "Balatian", 
        "Gipalitan", 
        "Dulaan", 
        "Naghilak",
        "Maghahakot"
    ]

    print(f"\n{'WORD':<15} | {'ROOT':<15} | {'ROOT POS':<10} | {'FINAL POS':<15}")
    print("-" * 65)
    
    for w in words:
        res = analyze_word(w)
        print(f"{res['original']:<15} | {res['root']:<15} | {res['root_pos']:<10} | {res['final_pos']:<15}")