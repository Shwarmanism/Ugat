"""
Pydantic schemas for API request/response validation.
Ugat-Lemmatizer Project
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# =========================
# Shared Models
# =========================

class LexiconEntry(BaseModel):
    """Entry in the lexicon search results."""
    term: str
    details: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    metadata: Dict[str, Any]


class LexiconSearchResponse(BaseModel):
    """Response for lexicon search."""
    items: List[LexiconEntry]
    total: int
    page: int
    total_pages: int



# =========================
# Request Schemas
# =========================

class TagRequest(BaseModel):
    """Request body for POS tagging endpoint."""
    text: str = Field(..., min_length=1, description="Text to tag")
    dialect: str = Field(..., description="Language dialect: ilocano, cebuano, hiligaynon")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Napan ti lalaki idiay merkado.",
                "dialect": "ilocano"
            }
        }


class LemmatizeRequest(BaseModel):
    """Request body for lemmatization endpoint."""
    text: str = Field(..., min_length=1, description="Text to lemmatize")
    dialect: str = Field(..., description="Language dialect: ilocano, cebuano, hiligaynon")
    mode: str = Field("crf", pattern="^(crf|affix)$", description="Tagging mode: crf or affix")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Napan ti lalaki idiay merkado.",
                "dialect": "ilocano"
            }
        }


# =========================
# Response Schemas
# =========================

class TokenResult(BaseModel):
    """Result for a single token."""
    token: str
    type: str  # irregular, root, function, morphed
    root: str
    pos: str
    affixes: List[str] = []
    stripped: str = ""


class SentenceResult(BaseModel):
    """Result for a single sentence."""
    tokens: List[TokenResult]


class TagResponse(BaseModel):
    """Response for POS tagging endpoint."""
    dialect: str
    input_text: str
    sentences: List[List[dict]]  # [[{token, pos}, ...], ...]
    
    class Config:
        json_schema_extra = {
            "example": {
                "dialect": "ilocano",
                "input_text": "Napan ti lalaki idiay merkado.",
                "sentences": [
                    [
                        {"token": "napan", "crf_pos": "VERB", "affix_pos": "VERB"},
                        {"token": "ti", "crf_pos": "DET", "affix_pos": "UNK"}
                    ]
                ]
            }
        }


class LemmatizeResponse(BaseModel):
    """Response for lemmatization endpoint."""
    dialect: str
    input_text: str
    sentences: List[List[TokenResult]]
    
    class Config:
        json_schema_extra = {
            "example": {
                "dialect": "ilocano",
                "input_text": "Napan ti lalaki idiay merkado.",
                "sentences": [
                    [
                        {"token": "napan", "type": "irregular", "root": "mapan", "pos": "VERB", "affixes": []},
                        {"token": "ti", "type": "function", "root": "ti", "pos": "DET", "affixes": []}
                    ]
                ]
            }
        }


class DialectsResponse(BaseModel):
    """Response for available dialects endpoint."""
    available_dialects: List[str]


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str