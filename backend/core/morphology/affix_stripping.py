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
        # Calculate path: morphology/ → core/ → backend/ → resources/
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
                        # Store the entire POS-based structure
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
                            # Expected format: {word: POS}
                            self.roots[lang] = {k.lower(): v for k, v in data.items()}
                        elif isinstance(data, list):
                            # Legacy format: [word, word, ...]
                            self.roots[lang] = {w.lower(): "UNKNOWN" for w in data}
                        
                        # Build set for O(1) lookup
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
        # Root dict may have: VERB, NOUN, ADJ, ADJECTIVE, ADVERB, etc.
        root_pos_normalized = root_pos
        if root_pos in ("ADJECTIVE", "JJ"):
            root_pos_normalized = "ADJ"
        elif root_pos in ("VB", "VBN", "VBG"):
            root_pos_normalized = "VERB"
        elif root_pos in ("NN", "NNS", "NNP"):
            root_pos_normalized = "NOUN"
        elif root_pos in ("ADVERB", "RB"):
            root_pos_normalized = "ADJ"  # Adverbs often share ADJ rules
        
        return normalized_target == root_pos_normalized
    
    def get_root_pos(self, word: str, lang: str) -> Optional[str]:
        """Get the POS of a root word, or None if not found."""
        return self.roots.get(lang, {}).get(word.lower())

    # --- Rule Extraction ---
    
    def get_rules_for_pos(self, lang: str, pos: str) -> Dict[str, List[str]]:
        """
        Get affix rules for a specific POS category.
        
        Args:
            lang: Language/dialect
            pos: POS tag (will be normalized)
        
        Returns:
            Dict with keys: prefixes, suffixes, infixes (flat lists)
        """
        # Normalize POS to rule category
        normalized_pos = self.POS_MAPPING.get(pos.upper(), pos.upper())
        
        # Get rules for this language
        lang_rules = self.AFFIX_DB.get(lang, {})
        pos_rules = lang_rules.get(normalized_pos, {})
        
        prefixes = []
        suffixes = []
        infixes = []
        
        # Extract from POS-specific rules
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
        """
        Get ALL affix rules for a language (all POS combined).
        Used as fallback when POS-specific rules don't yield a result.
        """
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
                # Infixes typically appear near the beginning
                if 0 < idx < 3:
                    candidate = word[:idx] + word[idx + len(infix):]
                    # If lang provided, validate against root dict
                    if lang and self.is_root(candidate, lang):
                        return candidate
                    elif not lang:
                        return candidate
        return word

    def strip_prefix(self, word: str, prefixes: List[str], lang: str = None) -> str:
        """
        Remove prefix with root validation.
        
        Strategy:
        1. Sort prefixes by length descending (try longest first)
        2. For each prefix, check if stripped result is a valid root
        3. If root found, return it (prefer valid roots over longest match)
        4. If no root found, return longest match as fallback
        """
        sorted_prefixes = sorted(prefixes, key=len, reverse=True)
        best_candidate = None
        
        for prefix in sorted_prefixes:
            if word.startswith(prefix):
                candidate = word[len(prefix):]
                
                # If lang provided, prioritize candidates that are valid roots
                if lang and self.is_root(candidate, lang):
                    return candidate  # Found a valid root, return immediately
                
                # Store first (longest) match as fallback
                if best_candidate is None:
                    best_candidate = candidate
        
        return best_candidate if best_candidate else word

    def strip_suffix(self, word: str, suffixes: List[str], lang: str = None) -> str:
        """
        Remove suffix with root validation.
        """
        sorted_suffixes = sorted(suffixes, key=len, reverse=True)
        best_candidate = None
        
        for suffix in sorted_suffixes:
            if word.endswith(suffix):
                candidate = word[:-len(suffix)]
                
                # If lang provided, prioritize candidates that are valid roots
                if lang and self.is_root(candidate, lang):
                    return candidate
                
                if best_candidate is None:
                    best_candidate = candidate
        
        return best_candidate if best_candidate else word

    def strip_reduplication(self, word: str) -> str:
        """Remove CV/CVC reduplication at word beginning."""
        if len(word) >= 4:
            # Check for CV-CV reduplication (e.g., "la-la" in "lalaki")
            if word[:2] == word[2:4]:
                return word[2:]
            # Check for CVC-CVC pattern
            if len(word) >= 6 and word[:3] == word[3:6]:
                return word[3:]
        return word

    # --- Main Lemmatize ---
    
    def lemmatize(self, word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
        """POS-aware lemmatization with infix → prefix → reduplication → suffix stripping."""
        lang = lang.lower()
        word = word.lower()
        original_word = word
        
        # Early exit if already a root
        if self.is_root(word, lang):
            return {
                "lemma": word,
                "rule": "Root Word",
                "status": "found",
                "affixes": [],
                "pos": self.get_root_pos(word, lang) or pos
            }
        
        # Get POS-specific rules
        if pos:
            rules = self.get_rules_for_pos(lang, pos)
            use_pos_validation = True
        else:
            # No POS provided, use all rules
            rules = self.get_all_rules(lang)
            use_pos_validation = False
        
        if not any(rules.values()):
            # No rules found for this POS, try all rules
            rules = self.get_all_rules(lang)
            use_pos_validation = False
        
        # Apply stripping with validation
        current_form = word
        applied_affixes = []
        
        # 2a. Infix stripping
        temp = self.strip_infix(current_form, rules["infixes"], lang)
        if temp != current_form:
            applied_affixes.append("infix")
            current_form = temp
            
            # Validate: must match same POS
            if use_pos_validation:
                if self.is_root_with_pos(current_form, lang, pos):
                    return {
                        "lemma": current_form,
                        "rule": "Infix Stripping",
                        "status": "found",
                        "affixes": applied_affixes,
                        "pos": pos
                    }
            elif self.is_root(current_form, lang):
                return {
                    "lemma": current_form,
                    "rule": "Infix Stripping",
                    "status": "found",
                    "affixes": applied_affixes,
                    "pos": self.get_root_pos(current_form, lang)
                }
        
        # 2b. Prefix stripping
        temp = self.strip_prefix(current_form, rules["prefixes"], lang)
        if temp != current_form:
            applied_affixes.append("prefix")
            current_form = temp
            
            if use_pos_validation:
                if self.is_root_with_pos(current_form, lang, pos):
                    return {
                        "lemma": current_form,
                        "rule": "Prefix Stripping",
                        "status": "found",
                        "affixes": applied_affixes,
                        "pos": pos
                    }
            elif self.is_root(current_form, lang):
                return {
                    "lemma": current_form,
                    "rule": "Prefix Stripping",
                    "status": "found",
                    "affixes": applied_affixes,
                    "pos": self.get_root_pos(current_form, lang)
                }
        
        # 2c. Reduplication stripping
        temp = self.strip_reduplication(current_form)
        if temp != current_form:
            applied_affixes.append("reduplication")
            current_form = temp
            
            if use_pos_validation:
                if self.is_root_with_pos(current_form, lang, pos):
                    return {
                        "lemma": current_form,
                        "rule": "Reduplication Stripping",
                        "status": "found",
                        "affixes": applied_affixes,
                        "pos": pos
                    }
            elif self.is_root(current_form, lang):
                return {
                    "lemma": current_form,
                    "rule": "Reduplication Stripping",
                    "status": "found",
                    "affixes": applied_affixes,
                    "pos": self.get_root_pos(current_form, lang)
                }
        
        # 2d. Suffix stripping
        temp = self.strip_suffix(current_form, rules["suffixes"], lang)
        if temp != current_form:
            applied_affixes.append("suffix")
            current_form = temp
            
            if use_pos_validation:
                if self.is_root_with_pos(current_form, lang, pos):
                    return {
                        "lemma": current_form,
                        "rule": "Suffix Stripping",
                        "status": "found",
                        "affixes": applied_affixes,
                        "pos": pos
                    }
            elif self.is_root(current_form, lang):
                return {
                    "lemma": current_form,
                    "rule": "Suffix Stripping",
                    "status": "found",
                    "affixes": applied_affixes,
                    "pos": self.get_root_pos(current_form, lang)
                }
        
        # 2e. Multi-pass: Try additional suffix after prefix
        if "prefix" in applied_affixes and "suffix" not in applied_affixes:
            temp = self.strip_suffix(current_form, rules["suffixes"], lang)
            if temp != current_form:
                applied_affixes.append("suffix")
                current_form = temp
                
                if use_pos_validation:
                    if self.is_root_with_pos(current_form, lang, pos):
                        return {
                            "lemma": current_form,
                            "rule": "Multi-pass Stripping",
                            "status": "found",
                            "affixes": applied_affixes,
                            "pos": pos
                        }
                elif self.is_root(current_form, lang):
                    return {
                        "lemma": current_form,
                        "rule": "Multi-pass Stripping",
                        "status": "found",
                        "affixes": applied_affixes,
                        "pos": self.get_root_pos(current_form, lang)
                    }
        
        # Relaxed validation - found as root but different POS
        if use_pos_validation and self.is_root(current_form, lang):
            return {
                "lemma": current_form,
                "rule": "Cross-POS Match",
                "status": "found",
                "affixes": applied_affixes,
                "pos": self.get_root_pos(current_form, lang)
            }
        
        # Fallback: try ALL rules if POS-specific didn't work
        if use_pos_validation and not applied_affixes:
            all_rules = self.get_all_rules(lang)
            fallback_form = word
            fallback_affixes = []
            
            # Try infix
            temp = self.strip_infix(fallback_form, all_rules["infixes"], lang)
            if temp != fallback_form:
                fallback_affixes.append("infix")
                fallback_form = temp
                if self.is_root(fallback_form, lang):
                    return {
                        "lemma": fallback_form,
                        "rule": "Infix Stripping (Fallback)",
                        "status": "found",
                        "affixes": fallback_affixes,
                        "pos": self.get_root_pos(fallback_form, lang)
                    }
            
            # Try prefix
            temp = self.strip_prefix(fallback_form, all_rules["prefixes"], lang)
            if temp != fallback_form:
                fallback_affixes.append("prefix")
                fallback_form = temp
                if self.is_root(fallback_form, lang):
                    return {
                        "lemma": fallback_form,
                        "rule": "Prefix Stripping (Fallback)",
                        "status": "found",
                        "affixes": fallback_affixes,
                        "pos": self.get_root_pos(fallback_form, lang)
                    }
            
            # Try suffix
            temp = self.strip_suffix(fallback_form, all_rules["suffixes"], lang)
            if temp != fallback_form:
                fallback_affixes.append("suffix")
                fallback_form = temp
                if self.is_root(fallback_form, lang):
                    return {
                        "lemma": fallback_form,
                        "rule": "Suffix Stripping (Fallback)",
                        "status": "found",
                        "affixes": fallback_affixes,
                        "pos": self.get_root_pos(fallback_form, lang)
                    }
            
            # Update current state for heuristic
            if fallback_affixes:
                current_form = fallback_form
                applied_affixes = fallback_affixes
        
        # Heuristic fallback for OOV words
        heuristic_result = self._heuristic_fallback(
            original_word, current_form, applied_affixes, rules, lang, pos
        )
        if heuristic_result:
            return heuristic_result
        
        # No match found
        return {
            "lemma": original_word,
            "rule": "None",
            "status": "not_found",
            "affixes": [],
            "pos": pos
        }

    # --- Heuristic Fallback (OOV) ---
    
    def _heuristic_fallback(
        self,
        original_word: str,
        current_form: str,
        applied_affixes: List[str],
        rules: Dict[str, List[str]],
        lang: str,
        pos: str
    ) -> Optional[Dict[str, Any]]:
        """Heuristic fallback for OOV words (hyphen stripping, accept stripped form)."""
        word = original_word.lower()
        prefixes = set(rules.get("prefixes", []))
        
        # Rule 1: Hyphen stripping for borrowed words (nag-text → text)
        if '-' in word:
            parts = word.split('-')
            
            if len(parts) == 2:
                prefix_part, stem_part = parts
                
                # Check if prefix matches known affix from rules
                if prefix_part in prefixes and len(stem_part) >= 3:
                    return {
                        "lemma": stem_part,
                        "rule": "Heuristic: Hyphen Stripping",
                        "status": "heuristic",
                        "affixes": [f"{prefix_part}-"],
                        "pos": pos
                    }
                
                # Short prefix (1-4 chars) with valid stem
                if len(prefix_part) <= 4 and len(stem_part) >= 3:
                    return {
                        "lemma": stem_part,
                        "rule": "Heuristic: Hyphen Stripping",
                        "status": "heuristic",
                        "affixes": [f"{prefix_part}-"],
                        "pos": pos
                    }
        
        # Rule 2: Accept stripped form if affixes were applied and stem >= 3 chars
        if applied_affixes and current_form != original_word:
            if len(current_form) >= 3:
                return {
                    "lemma": current_form,
                    "rule": f"Heuristic: {'+'.join(applied_affixes)} (OOV)",
                    "status": "heuristic",
                    "affixes": applied_affixes,
                    "pos": pos
                }
        
        return None


# Singleton instance
_engine_instance: Optional[MorphologicalEngine] = None


def get_morph_engine() -> MorphologicalEngine:
    """Get singleton instance of MorphologicalEngine."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = MorphologicalEngine()
    return _engine_instance


def lemmatize(word: str, lang: str = "cebuano", pos: str = None) -> Dict[str, Any]:
    """Convenience function for lemmatization."""
    return get_morph_engine().lemmatize(word, lang, pos)