"""
Core Module
Ugat-Lemmatizer Project

Central exports for preprocessing and tagging.
"""

# Preprocessing
from .preprocessing import tokenizer, segmenter

# Tagging
from .tagger import (
    crf_predict,
    affix_predict,
    format_tokens_for_crf,
    get_available_dialects,
)

__all__ = [
    # Preprocessing
    "tokenizer",
    "segmenter",
    # Tagging
    "crf_predict",
    "affix_predict", 
    "format_tokens_for_crf",
    "get_available_dialects",
]