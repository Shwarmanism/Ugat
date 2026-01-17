"""
API module for Ugat-Lemmatizer.
"""

from .routes import router
from .schemas import (
    TagRequest, TagResponse,
    LemmatizeRequest, LemmatizeResponse,
    DialectsResponse, TokenResult, ErrorResponse
)

__all__ = [
    "router",
    "TagRequest", "TagResponse",
    "LemmatizeRequest", "LemmatizeResponse",
    "DialectsResponse", "TokenResult", "ErrorResponse"
]
