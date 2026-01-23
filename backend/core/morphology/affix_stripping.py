import os
import json
from typing import Dict, List, Set, Optional, Any
from pathlib import Path

class MorphologicalEngine:
    POS_MAPPING = {
        "VERB": "VERB", "VB": "VERB", "VBN": "VERB", "VBG": "VERB",
        "NOUN": "NOUN", "NN": "NOUN", "NNS": "NOUN", "NNP": "NOUN",
        "ADJ": "ADJ", "JJ": "ADJ", "JJR": "ADJ", "JJS": "ADJ",
        "ADV": "ADJ", "RB": "ADJ",
    }
    
    def __init__(self):
        self.AFFIX_DB: Dict[str, Dict] = {}
        self.roots: Dict[str, Dict[str, str]] = {"cebuano": {}, "ilocano": {}, "hiligaynon": {}}
        self.root_sets: Dict[str, Set[str]] = {"cebuano": set(), "ilocano": set(), "hiligaynon": set()}
        # ✅ NEW: Dictionary to store irregular mappings
        self.irregulars: Dict[str, Dict[str, Any]] = {"cebuano": {}, "ilocano": {}, "hiligaynon": {}}
        self.load_resources()

    def load_resources(self):
        # 1. Robust Path Finding
        possible_paths = [
            Path(__file__).resolve().parents[3] / "resources",
            Path(__file__).resolve().parents[2] / "resources",
            Path(os.getcwd()) / "resources",
            Path(os.getcwd()) / "backend" / "resources",
        ]
        resource_path = next((p for p in possible_paths if p.exists()), None)
        
        if not resource_path: return

        languages = ["cebuano", "hiligaynon", "ilocano"]
        for lang in languages:
            # Load Affix Rules
            try:
                with open(resource_path / f"{lang.capitalize()}-rules.json", "r", encoding="utf-8") as f:
                    self.AFFIX_DB[lang] = json.load(f)
            except: pass
            
            # Load Roots
            try:
                with open(resource_path / f"root_{lang}.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict): self.roots[lang] = {k.lower(): v for k, v in data.items()}
                    elif isinstance(data, list): self.roots[lang] = {w.lower(): "UNKNOWN" for w in data}
                    self.root_sets[lang] = set(self.roots[lang].keys())
            except: pass

            # ✅ NEW: Load Irregulars
            try:
                with open(resource_path / f"irregular_{lang}.json", "r", encoding="utf-8") as f:
                    self.irregulars[lang] = json.load(f)
            except: pass

    def is_root(self, word: str, lang: str) -> bool:
        return word.lower() in self.root_sets.get(lang, set())
    
    def get_root_pos(self, word: str, lang: str) -> Optional[str]:
        return self.roots.get(lang, {}).get(word.lower())

    def get_rules_for_pos(self, lang: str, pos: str) -> Dict[str, List[str]]:
        normalized = self.POS_MAPPING.get(pos.upper(), pos.upper())
        rules = self.AFFIX_DB.get(lang, {}).get(normalized, {})
        
        prefixes, suffixes, infixes = [], [], []
        for r in rules.get("prefix_rules", []): prefixes.append(r["prefix"] if isinstance(r, dict) else r)
        for r in rules.get("suffix_rules", []): suffixes.append(r["suffix"] if isinstance(r, dict) else r)
        for r in rules.get("infix_rules", []): infixes.append(r["infix"] if isinstance(r, dict) else r)
        return {"prefixes": list(set(prefixes)), "suffixes": list(set(suffixes)), "infixes": list(set(infixes))}

    def get_all_rules(self, lang: str) -> Dict[str, List[str]]:
        lang_rules = self.AFFIX_DB.get(lang, {})
        combined = {"prefix_rules": [], "suffix_rules": [], "infix_rules": []}
        for pos_data in lang_rules.values():
            if isinstance(pos_data, dict):
                combined["prefix_rules"].extend(pos_data.get("prefix_rules", []))
                combined["suffix_rules"].extend(pos_data.get("suffix_rules", []))
                combined["infix_rules"].extend(pos_data.get("infix_rules", []))
        
        prefixes, suffixes, infixes = [], [], []
        for r in combined["prefix_rules"]: prefixes.append(r["prefix"] if isinstance(r, dict) else r)
        for r in combined["suffix_rules"]: suffixes.append(r["suffix"] if isinstance(r, dict) else r)
        for r in combined["infix_rules"]: infixes.append(r["infix"] if isinstance(r, dict) else r)
        return {"prefixes": list(set(prefixes)), "suffixes": list(set(suffixes)), "infixes": list(set(infixes))}

    # ✅ NEW HELPER: Checks if a word is a Root OR an Irregular form
    def _resolve_candidate(self, word: str, lang: str) -> Optional[str]:
        word_lower = word.lower()
        
        # 1. Check Irregular Dictionary First (e.g. "ubbing" -> "ubing")
        if word_lower in self.irregulars.get(lang, {}):
            return self.irregulars[lang][word_lower].get("equivalent", word_lower)
            
        # 2. Check Standard Root Dictionary
        if self.is_root(word_lower, lang):
            return word_lower
            
        return None

    def strip_infix(self, word: str, infixes: List[str], lang: str = None) -> str:
        for infix in infixes:
            if infix in word:
                idx = word.find(infix)
                if 0 < idx < 3:
                    candidate = word[:idx] + word[idx + len(infix):]
                    # Check if valid immediately
                    if lang and self._resolve_candidate(candidate, lang): return candidate
                    elif not lang: return candidate
        return word

    def strip_prefix(self, word: str, prefixes: List[str], lang: str = None) -> str:
        sorted_p = sorted(prefixes, key=len, reverse=True)
        for p in sorted_p:
            if word.startswith(p):
                cand = word[len(p):]
                if lang and self._resolve_candidate(cand, lang): return cand
        
        # Fallback for multi-stage stripping (keep largest match even if not root yet)
        for p in sorted_p:
            if word.startswith(p): return word[len(p):]
        return word

    def strip_suffix(self, word: str, suffixes: List[str], lang: str = None) -> str:
        sorted_s = sorted(suffixes, key=len, reverse=True)
        for s in sorted_s:
            if word.endswith(s):
                cand = word[:-len(s)]
                if lang and self._resolve_candidate(cand, lang): return cand
        
        for s in sorted_s:
            if word.endswith(s): return word[:-len(s)]
        return word

    def strip_reduplication(self, word: str, lang: str = None) -> str:
        if '-' in word:
            parts = word.split('-')
            # Case A: Full Identity
            if len(parts) >= 2 and all(p == parts[0] for p in parts):
                return parts[0]
            # Case B: Partial Prefix Identity (ub-ubbing -> ubbing)
            if len(parts) == 2:
                prefix, base = parts[0], parts[1]
                if base.startswith(prefix):
                    return base

        if len(word) >= 6 and len(word) % 2 == 0:
            half = len(word) // 2
            if word[:half] == word[half:]:
                cand = word[:half]
                if lang and self._resolve_candidate(cand, lang): return cand

        if len(word) >= 4:
            if word[:2] == word[2:4]: # CV
                cand = word[2:]
                if lang and self._resolve_candidate(cand, lang): return cand
                elif not lang: return cand
            if len(word) >= 6 and word[:3] == word[3:6]: # CVC
                cand = word[3:]
                if lang and self._resolve_candidate(cand, lang): return cand
                elif not lang: return cand
        return word

    def _attempt_stripping(self, word: str, lang: str, rules_pos: str = None):
        rules = self.get_rules_for_pos(lang, rules_pos) if rules_pos else self.get_all_rules(lang)
        if not any(rules.values()): return None
        
        current = word
        affixes = []

        # 1. Infix
        temp = self.strip_infix(current, rules["infixes"], lang)
        if temp != current:
            affixes.append("infix")
            current = temp
            # ✅ UPDATED: Use _resolve_candidate instead of is_root
            resolved = self._resolve_candidate(current, lang)
            if resolved: return self._build_result(resolved, "Infix", affixes, rules_pos, lang)

        # 2. Prefix
        while True:
            temp = self.strip_prefix(current, rules["prefixes"], lang)
            if temp == current: break
            affixes.append("prefix")
            current = temp
            resolved = self._resolve_candidate(current, lang)
            if resolved: return self._build_result(resolved, "Prefix", affixes, rules_pos, lang)

        # 3. Reduplication
        temp = self.strip_reduplication(current, lang)
        if temp != current:
            affixes.append("redup")
            current = temp
            
            # ✅ CRITICAL: Check irregulars immediately after redup strip
            # Example: "ub-ubbing" -> "ubbing" -> (resolve) -> "ubing"
            resolved = self._resolve_candidate(current, lang)
            if resolved: return self._build_result(resolved, "Redup", affixes, rules_pos, lang)
            
            # Recursive Prefix check (for "ag-agawid")
            temp_p = self.strip_prefix(current, rules["prefixes"], lang)
            if temp_p != current:
                affixes.append("prefix")
                current = temp_p
                resolved = self._resolve_candidate(current, lang)
                if resolved: return self._build_result(resolved, "Redup+Prefix", affixes, rules_pos, lang)

        # 4. Suffix
        temp = self.strip_suffix(current, rules["suffixes"], lang)
        if temp != current:
            affixes.append("suffix")
            current = temp
            resolved = self._resolve_candidate(current, lang)
            if resolved: return self._build_result(resolved, "Suffix", affixes, rules_pos, lang)
            
            # Recursive checks
            temp_infix = self.strip_infix(current, rules["infixes"], lang)
            if temp_infix != current:
                affixes.append("infix")
                current = temp_infix
                resolved = self._resolve_candidate(current, lang)
                if resolved: return self._build_result(resolved, "Suffix+Infix", affixes, rules_pos, lang)

            temp_prefix = self.strip_prefix(current, rules["prefixes"], lang)
            if temp_prefix != current:
                affixes.append("prefix")
                current = temp_prefix
                resolved = self._resolve_candidate(current, lang)
                if resolved: return self._build_result(resolved, "Suffix+Prefix", affixes, rules_pos, lang)

        return None

    def _heuristic_fallback(self, original_word: str, current_form: str, applied_affixes: List[str], rules: Dict[str, List[str]], lang: str, pos: str) -> Optional[Dict[str, Any]]:
        word = original_word.lower()
        prefixes = set(rules.get("prefixes", []))
        
        if '-' in word:
            parts = word.split('-')
            if len(parts) == 2:
                prefix_part, stem_part = parts
                if prefix_part in prefixes and len(stem_part) >= 3:
                    return { "lemma": stem_part, "rule": "Heuristic: Hyphen Stripping", "status": "heuristic", "affixes": [f"{prefix_part}-"], "pos": pos }
        return None

    def _build_result(self, lemma, rule, affixes, pos, lang):
        return { "lemma": lemma, "rule": rule, "status": "found", "affixes": affixes, "pos": self.get_root_pos(lemma, lang) or pos }

    def lemmatize(self, word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
        lang = lang.lower()
        word = word.lower()
        original_word = word
        
        # Check if input is ALREADY a root or irregular
        resolved = self._resolve_candidate(word, lang)
        if resolved:
            return self._build_result(resolved, "Root/Irregular", [], pos, lang)
        
        # STRICT POS MODE
        if pos:
            res = self._attempt_stripping(word, lang, pos)
            if res: return res
        else:
            res = self._attempt_stripping(word, lang, None)
            if res: return res

        # HEURISTICS
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
                    return { "lemma": stem_part, "rule": "Heuristic: Hyphen Stripping", "status": "heuristic", "affixes": [f"{prefix_part}-"], "pos": pos }
                if len(prefix_part) <= 4 and len(stem_part) >= 3:
                    return { "lemma": stem_part, "rule": "Heuristic: Hyphen Stripping", "status": "heuristic", "affixes": [f"{prefix_part}-"], "pos": pos }
        if applied_affixes and current_form != original_word:
            if len(current_form) >= 3:
                return { "lemma": current_form, "rule": f"Heuristic: {'+'.join(applied_affixes)} (OOV)", "status": "heuristic", "affixes": applied_affixes, "pos": pos }
        return None


_engine_instance: Optional[MorphologicalEngine] = None
def get_morph_engine() -> MorphologicalEngine:
    global _engine_instance
    if _engine_instance is None: _engine_instance = MorphologicalEngine()
    return _engine_instance

def lemmatize(word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
    return get_morph_engine().lemmatize(word, lang, pos)