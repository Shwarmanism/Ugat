import os
import json

class MorphologicalEngine:
    def __init__(self):
        # We no longer hardcode AFFIX_DB. We load it dynamically.
        self.AFFIX_DB = {}
        
        # Initialize root sets
        self.roots = {
            "cebuano": set(),
            "ilocano": set(),
            "hiligaynon": set()
        }
        
        # Load Resources
        self.load_resources()

    def load_resources(self):
        """
        Loads both Rules (*_rules.json) and Roots (root_*.json) from backend/resources
        """
        # Calculate path to 'backend/resources'
        current_dir = os.path.dirname(os.path.abspath(__file__)) 
        backend_dir = os.path.dirname(current_dir)               
        resource_path = os.path.join(backend_dir, "resources")   

        languages = ["cebuano", "hiligaynon", "ilocano"]

        for lang in languages:
            # 1. LOAD RULES (Affixes)
            rules_file = os.path.join(resource_path, f"rules_{lang}.json")
            if os.path.exists(rules_file):
                try:
                    with open(rules_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Store in AFFIX_DB using the language key
                        self.AFFIX_DB[lang] = data["rules"]
                        print(f" Loaded Rules for {lang}")
                except Exception as e:
                    print(f" Error loading rules for {lang}: {e}")
            else:
                print(f" Warning: Rules file missing: {rules_file}")
                # Fallback: Empty rules to prevent crashes
                self.AFFIX_DB[lang] = {"prefixes": [], "suffixes": [], "infixes": []}

            # 2. LOAD ROOTS (Dictionary)
            roots_file = os.path.join(resource_path, f"root_{lang}.json")
            if os.path.exists(roots_file):
                try:
                    with open(roots_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            self.roots[lang] = set(word.lower() for word in data)
                        print(f" Loaded {len(self.roots[lang])} roots for {lang}")
                except Exception as e:
                    print(f" Error loading roots for {lang}: {e}")
            else:
                print(f" Warning: Root file missing: {roots_file}")

    def is_root(self, word, lang):
        return word in self.roots.get(lang, set())

    # ==========================================
    # STRIPPING LOGIC (Unchanged)
    # ==========================================
    def strip_infix(self, word, infixes):
        for infix in infixes:
            if infix in word:
                idx = word.find(infix)
                if idx > 0 and idx < 3: 
                    return word[:idx] + word[idx+len(infix):]
        return word

    def strip_prefix(self, word, prefixes):
        sorted_prefixes = sorted(prefixes, key=len, reverse=True)
        for prefix in sorted_prefixes:
            if word.startswith(prefix):
                return word[len(prefix):]
        return word

    def strip_suffix(self, word, suffixes):
        sorted_suffixes = sorted(suffixes, key=len, reverse=True)
        for suffix in sorted_suffixes:
            if word.endswith(suffix):
                return word[:-len(suffix)]
        return word

    def strip_reduplication(self, word):
        if len(word) >= 4:
            if word.startswith(word[:2] + word[:2]): 
                return word[2:]
        return word

    # ==========================================
    # MAIN LEMMATIZE FUNCTION
    # ==========================================
    def lemmatize(self, word, lang="cebuano"):
        lang = lang.lower()
        
        # 1. Get rules for this language
        rules = self.AFFIX_DB.get(lang)
        if not rules:
            return {"lemma": word, "rule": "No Rules Found", "status": "error"}
        
        current_form = word
        
        # 2. Check Root (Early Exit 1)
        if self.is_root(current_form, lang):
             return {"lemma": current_form, "rule": "Root Word", "status": "found"}

        # 3. Infix
        temp = self.strip_infix(current_form, rules.get("infixes", []))
        if temp != current_form:
            current_form = temp
            if self.is_root(current_form, lang):
                return {"lemma": current_form, "rule": "Infix Stripping", "status": "found"}

        # 4. Prefix
        temp = self.strip_prefix(current_form, rules.get("prefixes", []))
        if temp != current_form:
            current_form = temp
            if self.is_root(current_form, lang):
                return {"lemma": current_form, "rule": "Prefix Stripping", "status": "found"}

        # 5. Reduplication
        temp = self.strip_reduplication(current_form)
        if temp != current_form:
            current_form = temp
            if self.is_root(current_form, lang):
                return {"lemma": current_form, "rule": "Redup Stripping", "status": "found"}

        # 6. Suffix
        temp = self.strip_suffix(current_form, rules.get("suffixes", []))
        if temp != current_form:
            current_form = temp
            if self.is_root(current_form, lang):
                return {"lemma": current_form, "rule": "Suffix Stripping", "status": "found"}

        return {"lemma": word, "rule": "None", "status": "not_found"}

# Simple Test
# Simple Test
if __name__ == "__main__":
    engine = MorphologicalEngine()
    
    print("\n" + "="*50)
    print("TESTING HILIGAYNON MORPHOLOGY")
    print("="*50)

    # Test Cases: (Input Word, Expected Root)
    test_cases = [
        ("nagbasa", "basa"),    # Prefix nag-
        ("magluto", "luto"),    # Prefix mag-
        ("kumain", "kain"),     # Infix -um-
        ("lutuan", "luto"),     # Suffix -an
        "ginabakal",            # Prefix gina- -> bakal
        "babalik",              # Reduplication -> balik
        "wala_sa_dict"          # Should fail (Not in root dict)
    ]

    for word in test_cases:
        # Handle tuple or string input
        w = word[0] if isinstance(word, tuple) else word
        
        # Run Lemmatization
        result = engine.lemmatize(w, lang="hiligaynon")
        
        # FIX: Use text instead of emojis
        status_icon = "[OK]" if result['status'] == 'found' else "[X] "
        
        print(f"{status_icon} Input: {w:<15} -> Lemma: {result['lemma']:<10} | Rule: {result['rule']}")

    print("\n" + "="*50)