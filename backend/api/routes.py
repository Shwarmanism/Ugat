"""
API routes for Ugat-Lemmatizer.
Endpoints for POS tagging and lemmatization.
"""

from fastapi import APIRouter, HTTPException
from .schemas import (
    TagRequest, TagResponse,
    LemmatizeRequest, LemmatizeResponse,
    DialectsResponse, TokenResult
)
from pipeline import text_preprocess, pos_tagging, process_tokens, SUPPORTED_DIALECTS

# Create router
router = APIRouter()

# Convert frozenset to list for API responses
VALID_DIALECTS = list(SUPPORTED_DIALECTS)


def validate_dialect(dialect: str) -> str:
    """Validate and normalize dialect name."""
    dialect = dialect.lower().strip()
    if dialect not in SUPPORTED_DIALECTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid dialect '{dialect}'. Valid options: {VALID_DIALECTS}"
        )
    return dialect


# =========================
# Endpoints
# =========================

@router.get("/dialects", response_model=DialectsResponse)
def get_dialects():
    """Get list of available dialects."""
    return DialectsResponse(available_dialects=VALID_DIALECTS)


@router.post("/tag", response_model=TagResponse)
def tag_text(request: TagRequest):
    """
    Perform POS tagging on input text.
    Returns both CRF-based and Affix-based POS predictions.
    """
    dialect = validate_dialect(request.dialect)
    
    try:
        # Step 1: Preprocess (segment + tokenize)
        preprocessed = text_preprocess(request.text, dialect)
        
        # Step 2: POS tagging (returns crf_tagged and affix_tagged)
        tagged = pos_tagging(preprocessed)
        
        return TagResponse(
            dialect=dialect,
            input_text=request.text,
            sentences=tagged["crf_tagged"]
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lemmatize", response_model=LemmatizeResponse)
def lemmatize_text(request: LemmatizeRequest):
    """
    Full lemmatization pipeline.
    Preprocesses text, tags POS, and extracts root words.
    """
    dialect = validate_dialect(request.dialect)
    
    try:
        # Step 1: Preprocess (segment + tokenize)
        preprocessed = text_preprocess(request.text, dialect)
        
        # Step 2: POS tagging
        tagged = pos_tagging(preprocessed)
        
        # Step 3: Process tokens (irregular check + morphology)
        processed = process_tokens(tagged)
        
        # Convert to response format
        result_sentences = []
        for sentence in processed["sentences"]:
            tokens = [
                TokenResult(
                    token=item["token"],
                    type=item["type"],
                    root=item["root"],
                    pos=item["pos"],
                    affixes=item.get("affixes", [])
                )
                for item in sentence
            ]
            result_sentences.append(tokens)
        
        return LemmatizeResponse(
            dialect=dialect,
            input_text=request.text,
            sentences=result_sentences
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ugat-lemmatizer"}
