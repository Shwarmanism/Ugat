import os
import json
from typing import Dict, List, Set, Optional, Any


class MorphologicalEngine:
    """
    Rule-based Morphological Analyzer with POS-Aware Affix Stripping.
    
    Algorithm:
    1. Check if word is already a root
    2. Apply POS-specific affix rules (infix → prefix → reduplication → suffix)
    3. Validate candidate against root dictionary
    4. Fallback to all rules if POS-specific fails
    5. Heuristic for OOV/borrowed words
    """
    
    # POS tag normalization mapping (CRF tags → rule categories)
    POS_MAPPING = {
        # Verbs
        "VERB": "VERB",
        "VB": "VERB",
        "VBN": "VERB",
        "VBG": "VERB",
        # Nouns
        "NOUN": "NOUN",
        "NN": "NOUN",
        "NNS": "NOUN",
        "NNP": "NOUN",
        # Adjectives
        "ADJ": "ADJ",
        "JJ": "ADJ",
        "JJR": "ADJ",
        "JJS": "ADJ",
        # Adverbs (often use ADJ rules)
        "ADV": "ADJ",
        "RB": "ADJ",
    }
    
    def __init__(self):
        # Rules per language: {lang: {POS: {prefix_rules, suffix_rules, ...}}}
        self.AFFIX_DB: Dict[str, Dict] = {}
        
        # Roots per language: {lang: {word: POS}}
        self.roots: Dict[str, Dict[str, str]] = {
            "cebuano": {},
            "ilocano": {},
            "hiligaynon": {}
        }
        
        # Root sets for fast O(1) membership check
        self.root_sets: Dict[str, Set[str]] = {
            "cebuano": set(),
            "ilocano": set(),
            "hiligaynon": set()
        }
        
        # Load all resources
        self.load_resources()

    def load_resources(self):
        """Load rules and roots from backend/resources."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        core_dir = os.path.dirname(current_dir)
        backend_dir = os.path.dirname(core_dir)
        resource_path = os.path.join(backend_dir, "resources")

        languages = ["cebuano", "hiligaynon", "ilocano"]

        for lang in languages:
            # Load rules (POS-based affix rules)
            rules_file = os.path.join(resource_path, f"{lang.capitalize()}-rules.json")
            
            if os.path.exists(rules_file):
                try:
                    with open(rules_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        self.AFFIX_DB[lang] = data
                        print(f" Loaded Rules for {lang}")
                except Exception as e:
                    print(f" Error loading rules for {lang}: {e}")
                    self.AFFIX_DB[lang] = {}
            else:
                print(f" Warning: Rules file missing: {rules_file}")
                self.AFFIX_DB[lang] = {}

            # Load roots (word → POS dictionary)
            roots_file = os.path.join(resource_path, f"root_{lang}.json")
            
            if os.path.exists(roots_file):
                try:
                    with open(roots_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        if isinstance(data, dict):
                            self.roots[lang] = {k.lower(): v for k, v in data.items()}
                        elif isinstance(data, list):
                            self.roots[lang] = {w.lower(): "UNKNOWN" for w in data}
                        
                        self.root_sets[lang] = set(self.roots[lang].keys())
                        print(f" Loaded {len(self.roots[lang])} roots for {lang}")
                        
                except Exception as e:
                    print(f" Error loading roots for {lang}: {e}")
            else:
                print(f" Warning: Root file missing: {roots_file}")

    # --- Root Validation ---
    
    def is_root(self, word: str, lang: str) -> bool:
        """Check if word exists in root dictionary."""
        return word.lower() in self.root_sets.get(lang, set())
    
    def is_root_with_pos(self, word: str, lang: str, target_pos: str) -> bool:
        """Check if word exists in root dictionary with matching POS."""
        word = word.lower()
        roots_dict = self.roots.get(lang, {})
        
        if word not in roots_dict:
            return False
        
        root_pos = roots_dict[word].upper()
        
        # Normalize the target POS
        normalized_target = self.POS_MAPPING.get(target_pos.upper(), target_pos.upper())
        
        # Check for POS compatibility
        root_pos_normalized = root_pos
        if root_pos in ("ADJECTIVE", "JJ"):
            root_pos_normalized = "ADJ"
        elif root_pos in ("VB", "VBN", "VBG"):
            root_pos_normalized = "VERB"
        elif root_pos in ("NN", "NNS", "NNP"):
            root_pos_normalized = "NOUN"
        elif root_pos in ("ADVERB", "RB"):
            root_pos_normalized = "ADJ"
        
        return normalized_target == root_pos_normalized
    
    def get_root_pos(self, word: str, lang: str) -> Optional[str]:
        """Get the POS of a root word, or None if not found."""
        return self.roots.get(lang, {}).get(word.lower())

    # --- Rule Extraction ---
    
    def get_rules_for_pos(self, lang: str, pos: str) -> Dict[str, List[str]]:
        """Get affix rules for a specific POS category."""
        normalized_pos = self.POS_MAPPING.get(pos.upper(), pos.upper())
        lang_rules = self.AFFIX_DB.get(lang, {})
        pos_rules = lang_rules.get(normalized_pos, {})
        
        prefixes = []
        suffixes = []
        infixes = []
        
        for rule in pos_rules.get("prefix_rules", []):
            if isinstance(rule, dict) and "prefix" in rule:
                prefixes.append(rule["prefix"])
            elif isinstance(rule, str):
                prefixes.append(rule)
        
        for rule in pos_rules.get("suffix_rules", []):
            if isinstance(rule, dict) and "suffix" in rule:
                suffixes.append(rule["suffix"])
            elif isinstance(rule, str):
                suffixes.append(rule)
        
        for rule in pos_rules.get("infix_rules", []):
            if isinstance(rule, dict) and "infix" in rule:
                infixes.append(rule["infix"])
            elif isinstance(rule, str):
                infixes.append(rule)
        
        return {
            "prefixes": list(set(prefixes)),
            "suffixes": list(set(suffixes)),
            "infixes": list(set(infixes))
        }
    
    def get_all_rules(self, lang: str) -> Dict[str, List[str]]:
        """Get ALL affix rules for a language (all POS combined)."""
        lang_rules = self.AFFIX_DB.get(lang, {})
        
        prefixes = set()
        suffixes = set()
        infixes = set()
        
        for pos, pos_rules in lang_rules.items():
            if not isinstance(pos_rules, dict):
                continue
                
            for rule in pos_rules.get("prefix_rules", []):
                if isinstance(rule, dict) and "prefix" in rule:
                    prefixes.add(rule["prefix"])
            
            for rule in pos_rules.get("suffix_rules", []):
                if isinstance(rule, dict) and "suffix" in rule:
                    suffixes.add(rule["suffix"])
            
            for rule in pos_rules.get("infix_rules", []):
                if isinstance(rule, dict) and "infix" in rule:
                    infixes.add(rule["infix"])
        
        return {
            "prefixes": list(prefixes),
            "suffixes": list(suffixes),
            "infixes": list(infixes)
        }

    # --- Stripping Operations ---
    
    def strip_infix(self, word: str, infixes: List[str], lang: str = None) -> str:
        """Remove infix if found near word beginning (position 1-2)."""
        for infix in infixes:
            if infix in word:
                idx = word.find(infix)
                if 0 < idx < 3:
                    candidate = word[:idx] + word[idx + len(infix):]
                    if lang and self.is_root(candidate, lang):
                        return candidate
                    elif not lang:
                        return candidate
        return word

    def strip_prefix(self, word: str, prefixes: List[str], lang: str = None) -> str:
        """Remove prefix with root validation."""
        sorted_prefixes = sorted(prefixes, key=len, reverse=True)
        best_candidate = None
        
        for prefix in sorted_prefixes:
            if word.startswith(prefix):
                candidate = word[len(prefix):]
                if lang and self.is_root(candidate, lang):
                    return candidate
                if best_candidate is None:
                    best_candidate = candidate
        
        return best_candidate if best_candidate else word

    def strip_suffix(self, word: str, suffixes: List[str], lang: str = None) -> str:
        """Remove suffix with root validation."""
        sorted_suffixes = sorted(suffixes, key=len, reverse=True)
        best_candidate = None
        
        for suffix in sorted_suffixes:
            if word.endswith(suffix):
                candidate = word[:-len(suffix)]
                if lang and self.is_root(candidate, lang):
                    return candidate
                if best_candidate is None:
                    best_candidate = candidate
        
        return best_candidate if best_candidate else word

    def strip_reduplication(self, word: str, lang: str = None) -> str:
        """
        Handle 3 types of reduplication for ALL POS:
        1. Hyphenated Full: araw-araw -> araw
        2. Non-hyphenated Full: arawaraw -> araw
        3. Partial (CV/CVC): lalaki -> laki, tatakbo -> takbo
        """
        
        # 1. Hyphenated Reduplication (e.g., araw-araw)
        if '-' in word:
            parts = word.split('-')
            # Check if all parts are identical (allows "basa-basa-basa")
            if len(parts) >= 2 and all(p == parts[0] for p in parts):
                return parts[0]

         

        # 2. Non-Hyphenated Full Reduplication (e.g., arawaraw)
        # Check if word is even length and halves are identical
        if len(word) >= 6 and len(word) % 2 == 0:
            half = len(word) // 2
            first_half = word[:half]
            second_half = word[half:]
            
            if first_half == second_half:
                # SAFEGUARD: Only strip if result is a valid root to avoid 
                # stripping words like "alaala" (root) or "paruparo" (root).
                if lang and self.is_root(first_half, lang):
                    return first_half
                # If no language is provided, we can't be safe, so we skip 
                # to avoid destroying valid non-reduplicated roots.
        
        # 3. Partial Reduplication (CV / CVC)
        if len(word) >= 4:
            # CV Reduplication (e.g., lalaki -> laki, susulat -> sulat)
            # Checks if first 2 chars are repeated
            if word[:2] == word[2:4]:
                candidate = word[2:]
                # Prefer validation if lang is available
                if lang and self.is_root(candidate, lang):
                    return candidate
                elif not lang:
                    return candidate
            
            # CVC Reduplication (e.g., magtatakbo -> takbo (after mag- stripped))
            # Checks if first 3 chars are repeated
            if len(word) >= 6 and word[:3] == word[3:6]:
                candidate = word[3:]
                if lang and self.is_root(candidate, lang):
                    return candidate
                elif not lang:
                    return candidate

        return word

    # --- Main Lemmatize ---
    
    def lemmatize(self, word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
        """
        POS-aware lemmatization with AUTOMATIC FALLBACK.
        """
        lang = lang.lower()
        word = word.lower()
        original_word = word
        
        # Early exit if already a root
        if self.is_root(word, lang):
            return self._build_result(word, "Root Word", [], pos, lang)
        
        # ---------------------------------------------------------
        # PASS 1: STRICT POS MODE
        # ---------------------------------------------------------
        # If a POS tag is provided, try ONLY those rules first.
        if pos:
            # We extract the logic into a helper method called _attempt_stripping
            result = self._attempt_stripping(word, lang, rules_pos=pos)
            if result: 
                return result
            
            # [THIS IS THE MISSING PERSISTENCE]
            # If we reach here, the Strict POS rules FAILED.
            # We now implicitly say: "The CRF tag might be wrong. Let's try ALL rules."
            
        # ---------------------------------------------------------
        # PASS 2: UNIVERSAL FALLBACK
        # ---------------------------------------------------------
        # Try stripping using ALL rules from ALL categories
        # We pass rules_pos=None to signal "use all rules"
        result = self._attempt_stripping(word, lang, rules_pos=None)
        if result: 
            return result

        # ---------------------------------------------------------
        # PASS 3: HEURISTICS (OOV)
        # ---------------------------------------------------------
        # If everything failed, try your heuristics
        rules_all = self.get_all_rules(lang)
        heuristic_result = self._heuristic_fallback(original_word, word, [], rules_all, lang, pos)
        if heuristic_result: return heuristic_result
        
        return {
            "lemma": original_word,
            "rule": "None",
            "status": "not_found",
            "affixes": [],
            "pos": pos
        }

    def _attempt_stripping(self, word: str, lang: str, rules_pos: str = None):
        """
        Helper method that runs the stripping pipeline once with a specific set of rules.
        """
        # 1. Select Rules
        if rules_pos:
            rules = self.get_rules_for_pos(lang, rules_pos)
            if not any(rules.values()): return None
            use_pos_validation = True
        else:
            rules = self.get_all_rules(lang)
            use_pos_validation = False

        current_form = word
        applied_affixes = []

        # 1. Infix
        temp = self.strip_infix(current_form, rules["infixes"], lang)
        if temp != current_form:
            applied_affixes.append("infix")
            current_form = temp
            if self.is_root(current_form, lang):
                 return self._build_result(current_form, "Infix Stripping", applied_affixes, rules_pos, lang)

        # 2. Prefix (Loop)
        while True:
            temp = self.strip_prefix(current_form, rules["prefixes"], lang)
            if temp == current_form: break
            applied_affixes.append("prefix")
            current_form = temp
            
            if use_pos_validation:
                if self.is_root_with_pos(current_form, lang, rules_pos):
                    return self._build_result(current_form, "Prefix Stripping", applied_affixes, rules_pos, lang)
            elif self.is_root(current_form, lang):
                 return self._build_result(current_form, "Prefix Stripping", applied_affixes, rules_pos, lang)

        # 3. Reduplication
        temp = self.strip_reduplication(current_form, lang)
        if temp != current_form:
            applied_affixes.append("reduplication")
            current_form = temp
            if self.is_root(current_form, lang):
                 return self._build_result(current_form, "Reduplication Stripping", applied_affixes, rules_pos, lang)

        # 4. Suffix
        temp = self.strip_suffix(current_form, rules["suffixes"], lang)
        if temp != current_form:
            applied_affixes.append("suffix")
            current_form = temp
            if self.is_root(current_form, lang):
                 return self._build_result(current_form, "Suffix Stripping", applied_affixes, rules_pos, lang)

        # 5. Multi-pass: Try additional suffix after prefix
        if "prefix" in applied_affixes and "suffix" not in applied_affixes:
            temp = self.strip_suffix(current_form, rules["suffixes"], lang)
            if temp != current_form:
                applied_affixes.append("suffix")
                current_form = temp
                if self.is_root(current_form, lang):
                    return self._build_result(current_form, "Multi-pass Stripping", applied_affixes, rules_pos, lang)

        # Relaxed validation (last resort match check)
        if not use_pos_validation and self.is_root(current_form, lang):
             return self._build_result(current_form, "Cross-POS Match", applied_affixes, rules_pos, lang)
        
        # ONLY return None if all steps failed
        return None

    def _build_result(self, lemma, rule, affixes, pos, lang):
        """Helper to format success result"""
        return {
            "lemma": lemma,
            "rule": rule,
            "status": "found",
            "affixes": affixes,
            "pos": self.get_root_pos(lemma, lang) or pos
        }

    def _heuristic_fallback(self, original_word: str, current_form: str, applied_affixes: List[str], rules: Dict[str, List[str]], lang: str, pos: str) -> Optional[Dict[str, Any]]:
        word = original_word.lower()
        prefixes = set(rules.get("prefixes", []))
        if '-' in word:
            parts = word.split('-')
            if len(parts) == 2:
                prefix_part, stem_part = parts
                if prefix_part in prefixes and len(stem_part) >= 3:
                    return { "lemma": stem_part, "rule": "Heuristic: Hyphen Stripping", "status": "heuristic", "affixes": ["prefix"], "pos": pos }
                if len(prefix_part) <= 4 and len(stem_part) >= 3:
                    return { "lemma": stem_part, "rule": "Heuristic: Hyphen Stripping", "status": "heuristic", "affixes": ["prefix"], "pos": pos }
        if applied_affixes and current_form != original_word:
            if len(current_form) >= 3:
                return { "lemma": current_form, "rule": f"Heuristic: {'+'.join(applied_affixes)} (OOV)", "status": "heuristic", "affixes": applied_affixes, "pos": pos }
        return None


_engine_instance: Optional[MorphologicalEngine] = None

def get_morph_engine() -> MorphologicalEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MorphologicalEngine()
    return _engine_instance

def lemmatize(word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
    return get_morph_engine().lemmatize(word, lang, pos)