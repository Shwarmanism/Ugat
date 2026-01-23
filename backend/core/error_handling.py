import re

class DialectVerifier:
    def __init__(self):
        # 1. EXCLUSIVE / STRONG MARKERS (Score: 5 points)
        # These words or roots STRONGLY indicate a specific dialect.
        # Derived from your 'roots' and common function words.
        self.strong_markers = {
            "ilocano": {
                # Function words
                "ti", "iti", "idiay", "wen", "met", "ngem", "pay", "kadi", "manen", 
                "toy", "dyay", "kuna", "ubing", "apan", "mapan", "ditoy", "daytoy",
                "isuna", "kaniana", "ani", "ania", "sino", "asin", "mano", 
                # Pronouns (Suffixes often appear as separate tokens in loose text)
                "tayo", "kayo", "dakayo", "datayo", "sikayo", "sika",
                # Common Roots
                "mangan", "nangan", "balasang", "adal", "surat", "biag"
            },
            "cebuano": {
                # Function words
                "ug", "og", "ka", "ko", "mo", "kini", "kana", "dinhi", "didto", 
                "unsa", "nganong", "mao", "karon", "diri", "ganina", "niini", "niiana",
                # Pronouns (Exclusive forms)
                "ikaw", "siya", "kita", "sila", "namo", "nato", "nila", "ninyo",
                # Common Roots
                "iro", "dagan", "balay", "kaon", "palit", "buhat", "gwapa", "ngil-ad"
            },
            "hiligaynon": {
                # Function words
                "sang", "kay", "subong", "gid", "gin", "sini", "sina", "wala", 
                "indi", "may", "kagina", "didto", "dira", "amo", "ngaa", "ano",
                # Pronouns (Exclusive forms)
                "akon", "imon", "iya", "namon", "naton", "inyo", "niya",
                # Common Roots
                "ido", "dalagan", "balay", "kaon", "bakal", "obra", "maanyag", "law-ay"
            }
        }

        # 2. SHARED / WEAK MARKERS (Score: 1 point)
        # Words common across Visayan languages (Ceb/Hil) or Tagalog overlaps.
        # These provide context but don't decide the winner alone.
        self.weak_markers = {
            "ang", "mga", "ni", "si", "sa", "na", "ba", "pa", "nag", "mag", "man", "ka"
        }

        # 3. DISTINCTIVE AFFIXES (Score: 3 points)
        # These are derived from your JSON "prefix_rules".
        # We prioritize the ones that are unique to that grammar.
        self.affixes = {
            "ilocano": [
                "ag-", "nag-", "manag-", "panag-", "mang-", "nakapag-", "makapag-"
            ], 
            "cebuano": [
                "mo-", "gi-", "mi-", "ni-", "nagka-", "magka-", "pakig-", "pagaka-"
            ],
            "hiligaynon": [
                "gina-", "naga-", "maga-", "nagaka-", "magaka-", "mangin-", "nangin-"
            ]
        }

    def get_confidence(self, text: str, selected_dialect: str) -> dict:
        text = text.lower()
        words = re.findall(r'\w+', text)
        
        if not words:
            return {"confidence": 0.0, "detected": None, "is_match": False}

        # Initialize scores
        scores = {"ilocano": 0, "cebuano": 0, "hiligaynon": 0}
        
        for word in words:
            # A. Check Strong Markers (The "Smoking Gun")
            for dialect, markers in self.strong_markers.items():
                if word in markers:
                    scores[dialect] += 5
            
            # B. Check Weak Markers (Shared context)
            if word in self.weak_markers:
                # 'ang', 'mga', 'si', 'ug', 'og' are strong indicators of Visayan (Ceb/Hil) vs Ilocano
                if word in ["ang", "mga", "si", "ug", "og", "sa"]: 
                    scores["cebuano"] += 1
                    scores["hiligaynon"] += 1
                # 'ni', 'nag', 'mag' are used in all, but mostly exclude Tagalog-only inputs
                if word in ["ni", "nag", "mag"]:
                    scores["ilocano"] += 1
                    scores["cebuano"] += 1
                    scores["hiligaynon"] += 1

            # C. Check Affixes (Prefix matching)
            # We check if the word *starts with* the unique prefix
            for dialect, prefix_list in self.affixes.items():
                for prefix in prefix_list:
                    # Remove hyphen for checking
                    clean_prefix = prefix.replace("-", "")
                    # Ensure word is longer than prefix + 2 letters to avoid false positives
                    if word.startswith(clean_prefix) and len(word) > len(clean_prefix) + 2:
                        scores[dialect] += 3
                        break # Count only one prefix per word per dialect

        # ---------------------------------------------------------
        # DECISION LOGIC
        # ---------------------------------------------------------
        total_score = sum(scores.values())
        best_dialect = max(scores, key=scores.get)
        
        # If total score is 0, we have no linguistic signal.
        # Assume match (benefit of the doubt) or return Unknown.
        if total_score == 0:
            return {
                "confidence": 0.0,
                "detected": selected_dialect, 
                "is_match": True,
                "scores": scores
            }

        selected_score = scores.get(selected_dialect, 0)
        
        # Confidence = How much of the total "signal" points to the user's choice?
        user_confidence = selected_score / total_score

        # ---------------------------------------------------------
        # THRESHOLDING (Tuning)
        # ---------------------------------------------------------
        is_match = True
        
        # Rule 1: Zero score for selection but high score for others
        if selected_score == 0 and total_score >= 3:
            is_match = False
            
        # Rule 2: Detected dialect is overwhelmingly stronger (e.g., > 1.5x score)
        # We lowered the threshold slightly because Hiligaynon/Cebuano are very close.
        elif scores[best_dialect] > (selected_score * 1.5):
            is_match = False

        return {
            "confidence": round(user_confidence, 2),
            "detected": best_dialect,
            "is_match": is_match,
            "scores": scores
        }