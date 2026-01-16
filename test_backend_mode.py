import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_lemmatize(text, dialect, mode):
    url = f"{BASE_URL}/lemmatize"
    payload = {
        "text": text,
        "dialect": dialect,
        "mode": mode
    }
    
    print(f"\n--- Testing Mode: {mode} ---")
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        # Print a snippet of the result to verify structure
        for sent in data["sentences"]:
            for token in sent:
                print(f"Token: {token['token']:<15} Pos: {token['pos']:<10} Root: {token['root']}")
                
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
             print(e.response.text)

if __name__ == "__main__":
    print("Verifying Backend API...")
    # Test text (Hiligaynon)
    text = "Nagkaon ang bata" 
    
    # Test CRF Mode
    test_lemmatize(text, "hiligaynon", "crf")
    
    # Test Affix Mode
    test_lemmatize(text, "hiligaynon", "affix")
