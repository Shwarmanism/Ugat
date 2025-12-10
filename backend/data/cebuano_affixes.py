# cebuano_affixes.py

# PREFIXES: Sorted by length (Longest first is CRITICAL)
# Added 'ng' and 'g' to handle contractions like 'ngdugo' -> 'dugo'
PREFIXES = [
    "di", "dili", "ga", "gai", "gaipa", "gaka", "gapa", "gapan", "gapang", "gi", "gihi", "gika", "gikahi", "gikapa", "gina", "ginapa", 
    "ginapaha", "ginapaka", "ginapag", "ginapang", "ginapanghi", "gipa", "gipaha", "gipahi", "gipaka", "gipaki", "gipakig", "gipanag", 
    "gipanig", "gipatig", "gipan", "gipang", "gipanghi", "gim", "gin", "ging", "ha", "hi", "hika", "hima", "hinga", "hipang", "hin", 
    "hing", "hingka", "i", "iga", "igaha", "igaka", "igapa", "igapaha", "igapahi", "igapaka", "igapasi", "igapang", "ihi", "ika", 
    "ikahi", "ikapa", "ikapakama", "ikapanig", "ikapasig", "ikapang", "ikag", "inig", "inighi", "inigka", "inigpa", "inigpang", 
    "inigpanghi", "ipa", "ipaha", "ipahi", "ipaka", "ipaki", "ipakig", "ipanig", "ipasig", "ipatig", "ipam", "ipampa", "ipang", 
    "ipanghi", "isig", "isigka", "itag", "ig", "igka", "igpa", "igpang", "ing", "ka", "kaha", "kahi", "kahing", "kama", "kapa", 
    "kapanig", "kapasi", "kapang", "kataga", "katagi", "katigi", "kina", "ma", "maga", "magaka", "magama", "magapa", "magapaha", 
    "magapahi", "magapaka", "magapaki", "magapakig", "magapan", "magapang", "maha", "mahag", "mahi", "mai", "maipa", "maipang", 
    "maka", "makahi", "makapa", "makapaha", "makapahi", "makapan", "makapang", "makapanghi", "makag", "maki", "makipag", "makig", 
    "makigpa", "makigpang", "manag", "managka", "managpa", "managpaka", "managpaki", "managpan", "managpang", "manga", "mangaha", 
    "manging", "mangim", "mangin", "mani", "manig", "manim", "mapa", "mapahi", "mapanag", "mapasig", "mapang", "masig", "masigka", 
    "matag", "mag", "maghi", "magka", "magkahi", "magkina", "magma", "magpa", "magpahi", "magpahing", "magpaka", "magpaki", 
    "magpakig", "magpasig", "magpang", "mam", "man", "mang", "manggi", "manghi", "mi", "mihi", "mikapa", "mipa", "mipaha", "mipahi", 
    "mipaka", "mipatig", "mipanghi", "misag", "ming", "mingpa", "mingpaha", "mo", "mohi", "mopa", "mopahi", "mopasig", "mopatig", 
    "na", "naga", "nagaha", "nagahi", "nagaka", "nagakahi", "nagama", "nagapa", "nagapaha", "nagapahi", "nagapaka", "nagapaki", 
    "nagapakig", "nagapan", "nagapang", "nagapanghi", "naha", "nahapa", "nahag", "nahi", "nahipa", "nai", "naipa", "naipang", 
    "naka", "nakahi", "nakapa", "nakapaha", "nakapahi", "nakapakig", "nakapasig", "nakapan", "nakapang", "nakapanghi", "nakag", 
    "naki", "nakipag", "nakig", "nakighi", "nakigpa", "nakigpang", "nanag", "nanagka", "nanagpa", "nanagpahi", "nanagpaka", 
    "nanagpaki", "nanagpakig", "nanagpan", "nanagpang", "nanagpangha", "nanagpanghi", "nanang", "nanga", "nangaha", "nangaka", 
    "nangag", "nangin", "nani", "nanig", "nanim", "naning", "napa", "napahi", "napasig", "napang", "nasig", "nag", "naghi", 
    "naghing", "nagisig", "nagka", "nagkahi", "nagkina", "nagma", "nagni", "nagpa", "nagpaha", "nagpahi", "nagpahing", 
    "nagpaka", "nagpaki", "nagpakig", "nagpanga", "nagpaning", "nagpasig", "nagpatig", "nagpan", "nagpang", "nagtika", "nagtig", 
    "nan", "nang", "nanggi", "nanghi", "nanghing", "ni", "nikapa", "nipa", "nipaka", "nipatig", "nipanghi", "ning", "ningpa", 
    "pa", "paga", "pagahi", "pagaka", "pagapa", "pagapaka", "pagapang", "paha", "pahi", "pahig", "paka", "paki", "pakig", 
    "pakigpa", "pala", "panag", "panagka", "panga", "pangang", "pangin", "pani", "panig", "panim", "papang", "para", "parag", 
    "pasi", "pasig", "pasing", "pati", "patig", "pag", "paghi", "paghig", "pagka", "pagkadi", "pagkadili", "pagkaha", "pagkahi", 
    "pagkama", "pagkawalay", "pagkaway", "pagkig", "pagma", "pagna", "pagni", "pagpa", "pagpaha", "pagpahi", "pagpaka", 
    "pagpaki", "pagpakig", "pagpanag", "pagpanga", "pagpangin", "pagpanim", "pagpasi", "pagpasig", "pagpasing", "pagpan", 
    "pagpang", "pagpanghi", "pam", "pampa", "pan", "pang", "panggi", "panghi", "pangpa", "pangpaka", "pangpang", "pina", 
    "pinaka", "sika", "taga", "tagi", "tali", "tag", "tagma", "tagmang", "tagpa", "tinag", "tig", "tigpa", "tigpaha", "tigpahi", 
    "tigpaka", "tigpaki", "tigpang", "tigpanghi", "ting", "tingpa", "tingpanga", "tingpang", "wa", "wala", "walay", "way",
    "ng", "g" # <--- ADDED THESE NEW PREFIXES
]
# Ensure longest prefixes are checked first (e.g., 'nag' before 'ng')
PREFIXES = sorted(list(set(PREFIXES)), key=len, reverse=True)

INFIXES = [ "in", "um", "al", "il", "ul" ]

SUFFIXES = [
    "a", "ado", "an", "anan", "anang", "anay", "ang", "anon", "anong", "ay", "ayg", "ayng", "do", "dor", "g", "ha", "hag", "han", 
    "hana", "hanan", "hanay", "hang", "hanon", "hanong", "hay", "hi", "hig", "hing", "hon", "hona", "hong", "honon", "i", "ig", 
    "ing", "ira", "irang", "iro", "irong", "n", "ng", "nhan", "nhon", "nhong", "nhonon", "non", "nong", "on", "onan", "ong", 
    "onon", "onong", "y", "yng"
]
SUFFIXES = sorted(list(set(SUFFIXES)), key=len, reverse=True)

# ==========================================
# AFFIX POS CATEGORIES
# ==========================================
# This tells the analyzer what an affix "turns the word into".

AFFIX_CATEGORIES = {
    # --- VERB AFFIXES (Action Makers) ---
    "mag": "v", "nag": "v", "pag": "v",
    "nagka": "v", "magka": "v", "pagka": "v",
    "mo": "v", "mi": "v", "mu": "v",
    "na": "v", "ma": "v", # 'ma' can be adj, but usually verb in derivation
    "gi": "v", "gina": "v",
    "mang": "v", "nang": "v", "pang": "v",
    "ipa": "v", "ika": "v",
    "gipa": "v", "gika": "v",
    "maka": "v", "naka": "v",
    "makig": "v", "nakig": "v",
    "man": "v", "nan": "v",
    "ng": "v", "g": "v", # Short forms of nag/gi
    
    # Suffixes that usually make Verbs
    "on": "v", "hon": "v", 
    "an": "v", "han": "v", # Can be Locative Noun, but often Verb (e.g., "ulanan" - rained on)
    
    # --- NOUN AFFIXES (Thing/Person Makers) ---
    "ka": "n",      # ka-gwapa (noun)
    "isig": "n",    # isigkatawo (fellow man)
    "taga": "n",    # tagabukid (from the mountain)
    "tig": "n",     # tigluto (cook)
    "tag": "n",     # tag-iya (owner)
    "ig": "n",      # ig-agaw (cousin)
    
    # Suffixes that make Nouns
    "anan": "n",    # kan-anan (eatery/place)
    "hanan": "n",
    "onon": "n",    # buhatonon (tasks)
    "dor": "n",
    "ero": "n",
    "ismo": "n",
    
    # --- ADJECTIVE AFFIXES (Descriptive) ---
    "ma": "adj",    # ma-anindot (beautiful) - *Context dependent*
    "ha": "adj",    # ha-t-as (high)
    "maka": "adj",  # maka-boang (maddening)
    "pina": "adj",  # pinirito (fried)
}

# Helper to look up an affix safely
def get_affix_pos(affix_str):
    # Strip hyphens for lookup (e.g., "mag-" -> "mag")
    clean = affix_str.replace("-", "").strip()
    return AFFIX_CATEGORIES.get(clean, "neutral") # Returns 'neutral' if unknown