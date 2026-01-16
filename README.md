# Ugat-Lemmatizer

A morphological analyzer and lemmatizer for Philippine regional languages. **Ugat** (meaning "root" in Filipino) extracts root words from inflected forms using both machine learning and rule-based approaches.

## Supported Languages

| Language | Region | Model Accuracy |
|----------|--------|----------------|
| **Ilocano** | Northern Luzon | 98.2% |
| **Cebuano** | Visayas | 97.3% |
| **Hiligaynon** | Western Visayas | 95.6% |

## Features

- **POS Tagging** - Two approaches:
  - CRF-based (Conditional Random Fields)
  - Affix-based (Rule-based pattern matching)
- **Lemmatization** - Root word extraction
- **Token Classification** - Irregular, root, function words, morphed
- **REST API** - FastAPI endpoints for integration

## Project Structure

```
Ugat-Lemmatizer/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── pipeline.py          # Main NLP processing pipeline
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── routes.py        # API endpoints
│   │   └── schemas.py       # Pydantic models
│   ├── core/
│   │   ├── preprocessing/   # Tokenizer, segmenter
│   │   ├── tagger/          # CRF & Affix taggers
│   │   └── morphology/      # Morphological rules
│   └── resources/           # Language data files
│       ├── *_crf_formatted.txt    # CRF training data
│       ├── *-rules.json           # Affix rules
│       ├── root_*.json            # Root word dictionaries
│       └── irregular_*.json       # Irregular word mappings
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── styles.css
├── .env                     # Environment variables
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Ugat-Lemmatizer.git
   cd Ugat-Lemmatizer
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Train CRF models** (if not already trained)
   ```bash
   cd backend/core/tagger
   python train_models.py
   ```

5. **Run the server**
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

6. **Access the API**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dialects` | List available dialects |
| `POST` | `/api/v1/tag` | POS tagging (CRF + Affix) |
| `POST` | `/api/v1/lemmatize` | Full lemmatization pipeline |
| `GET` | `/api/v1/health` | Health check |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/lemmatize" \
  -H "Content-Type: application/json" \
  -d '{"text": "Napan ti lalaki idiay merkado.", "dialect": "ilocano"}'
```

### Example Response

```json
{
  "dialect": "ilocano",
  "input_text": "Napan ti lalaki idiay merkado.",
  "sentences": [
    [
      {"token": "napan", "type": "irregular", "root": "mapan", "pos": "VERB", "affixes": []},
      {"token": "ti", "type": "function", "root": "ti", "pos": "DET", "affixes": []},
      {"token": "lalaki", "type": "root", "root": "lalaki", "pos": "NOUN", "affixes": []},
      {"token": "idiay", "type": "function", "root": "idiay", "pos": "ADP", "affixes": []},
      {"token": "merkado", "type": "root", "root": "merkado", "pos": "NOUN", "affixes": []}
    ]
  ]
}
```

## Pipeline Flow

```
Input Text
    ↓
┌─────────────────┐
│ 1. Preprocess   │ → Segment sentences + Tokenize
└─────────────────┘
    ↓
┌─────────────────┐
│ 2. POS Tagging  │ → CRF-based + Affix-based
└─────────────────┘
    ↓
┌─────────────────┐
│ 3. Process      │ → Classify token type:
│    Tokens       │   • Irregular → lookup mapping
│                 │   • Root → direct match
│                 │   • Function → DET/CONJ/PRON/etc.
│                 │   • Morphed → apply rules
└─────────────────┘
    ↓
Output JSON
```

## Token Types

| Type | Description | Example |
|------|-------------|---------|
| `irregular` | Irregular word form | napan → mapan |
| `root` | Already a root word | lalaki → lalaki |
| `function` | Function word (DET, CONJ, etc.) | ti, ken, daytoy |
| `morphed` | Needs morphological analysis | nagsurat → surat |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Authors

- Ugat-Lemmatizer Team

## Acknowledgments

- CRF implementation: sklearn-crfsuite
- Philippine linguistics resources
