from pipeline import main_pipeline, preload_all
import re

# Preload resources
preload_all()

# Run main pipeline
print("--- Running Main Pipeline ---")
result = main_pipeline("Nagkaon ang bata sa balay.", "hiligaynon")

# Inspect content
print("\nFinal Tokens Output:")
for token in result["tokens"]:
    print(f"Token: '{token['token']}'")
    print(f"POS:   '{token['pos']}'")
    print(f"Type:  '{token['type']}'")
    print(f"Affixes: {token.get('affixes')}")
    print(f"Stripped: '{token.get('stripped')}'")
    print(f"Lemma: '{token['lemma']}'")
    print("-" * 20)
    for token in sent:
        print(f"Token: '{token['token']}'")
        print(f"Root:  '{token['root']}'")
        print(f"Affixes: {token.get('affixes')}")
        print(f"Stripped: '{token.get('stripped', 'MISSING')}'")
        
        # Test my regex logic manually to verify
        if token['type'] == 'morphed':
             manual_stripped = re.sub(re.escape(token['root']), "", token['token'], flags=re.IGNORECASE)
             print(f"Manual Regex Check: '{manual_stripped}'")
        print("-" * 20)
