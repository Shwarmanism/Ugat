"""
API routes for Ugat-Lemmatizer.
Endpoints for POS tagging and lemmatization.
"""

from fastapi import APIRouter, HTTPException
from .schemas import (
    TagRequest, TagResponse,
    LemmatizeRequest, LemmatizeResponse,
    DialectsResponse, TokenResult,
    LexiconSearchResponse, LexiconEntry
)
from pipeline import (
    text_preprocess, pos_tagging, process_tokens, 
    SUPPORTED_DIALECTS, load_roots, load_irregular, load_rules
)

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


@router.get("/lexicon", response_model=LexiconSearchResponse)
def search_lexicon(
    type: str,
    dialect: str,
    q: str = "",
    page: int = 1,
    page_size: int = 50
):
    """
    Search lexicon resources (roots, irregulars, affixes).
    Supports partial text search and pagination.
    """
    dialect = validate_dialect(dialect)
    type = type.lower()
    
    # Load data based on type
    data = {}
    if type == "roots":
        data = load_roots(dialect)
    elif type == "irregular":
        data = load_irregular(dialect)
    elif type == "affixes":
        data = load_rules(dialect)
    else:
        raise HTTPException(
            status_code=400, 
            detail="Invalid type. Must be 'roots', 'irregular', or 'affixes'"
        )

    # Convert to list of LexiconEntry
    items = []
    
    # Handle different data structures
    if type == "roots":
        # Structure: {root: pos}
        for root, pos in data.items():
            items.append(LexiconEntry(
                term=root,
                details=pos,
                metadata={"type": "root"}
            ))
            
    elif type == "irregular":
        # Structure: {inflected: {equivalent, pos}}
        for inflected, info in data.items():
            # Check if info is dict or just string (handle inconsistencies)
            if isinstance(info, dict):
                items.append(LexiconEntry(
                    term=inflected,
                    details=info,
                    metadata={"type": "irregular"}
                ))
            else:
                 items.append(LexiconEntry(
                    term=inflected,
                    details={"equivalent": info, "pos": "UNK"},
                    metadata={"type": "irregular"}
                ))
            
    elif type == "affixes":
        # Structure: {POS: {prefix_rules: [...], ...}}
        # Flattening allows searching by affix string
        for pos_category, rules in data.items():
            # Process prefix, suffix, infix rules
            for rule_type, rule_list in rules.items():
                if isinstance(rule_list, list):
                    for rule in rule_list:
                        # Extract the actual affix string (prefix, suffix, infix)
                        affix_key = next((k for k in rule if k in ["prefix", "suffix", "infix"]), None)
                        if affix_key:
                            term = rule[affix_key]
                            items.append(LexiconEntry(
                                term=term,
                                details=rule,
                                metadata={
                                    "type": "affix",
                                    "pos": pos_category,
                                    "affix_type": affix_key
                                }
                            ))

    # Filter by query
    if q:
        q = q.lower()
        items = [i for i in items if q in i.term.lower()]
    
    # Sort items by term
    items.sort(key=lambda x: x.term)

    # Pagination
    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = items[start:end]
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

    return LexiconSearchResponse(
        items=paginated_items,
        total=total,
        page=page,
        total_pages=total_pages
    )


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
        processed = process_tokens(tagged, mode=request.mode)
        
        # Convert to response format
        result_sentences = []
        for sentence in processed["sentences"]:
            tokens = [
                TokenResult(
                    token=item["token"],
                    type=item["type"],
                    root=item["root"],
                    pos=item["pos"],
                    affixes=item.get("affixes", []),
                    stripped=item.get("stripped", "")
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