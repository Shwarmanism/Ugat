from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

# 1. ALLOW CONNECTION FROM FRONTEND (CORS)
# This allows your HTML file (running in browser) to talk to this Python script
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. DEFINE DATA MODELS (Matches the JSON in your script.js)
class ShowDetails(BaseModel):
    pos_tags: bool
    candidates: bool
    rules: bool
    lexicon_match: bool

class Preprocessing(BaseModel):
    remove_punctuation: bool
    normalize_caps: bool
    remove_numbers: bool

class Settings(BaseModel):
    show_details: ShowDetails
    preprocessing: Preprocessing
    output_format: str

class LemmatizeRequest(BaseModel):
    input_text: str
    dialect: str
    settings: Settings

# 3. THE ENDPOINT
@app.post("/api/lemmatize")
async def lemmatize(payload: LemmatizeRequest):
    print(f"Received text: '{payload.input_text}' | Dialect: {payload.dialect}")
    
    # --- [START] YOUR ACTUAL NLP LOGIC HERE ---
    # You can import your own functions here. 
    # For now, this is a placeholder that just returns the words as-is.
    
    words = payload.input_text.split()
    results = []
    
    for word in words:
        # Example logic: just assume everything is a noun for now
        results.append({
            "token": word,
            "lemma": word.lower(),  # Replace with real lemmatizer
            "pos": "Noun",          # Replace with real POS tagger
            "affixes": [],
            "candidates": [word.lower()],
            "rule": "Default",
            "is_irregular": False
        })
    # --- [END] YOUR ACTUAL NLP LOGIC HERE ---

    return {
        "detected_dialect": "Tagalog" if payload.dialect == "auto" else payload.dialect,
        "stats": {
            "tokens": len(words),
            "lemmas": len(words),
            "irregulars": 0
        },
        "results": results
    }

# Run this with: uvicorn main:app --reload
