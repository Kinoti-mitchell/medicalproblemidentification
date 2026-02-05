"""
Text normalization for consistent matching between user input and knowledge base.
Medical decision: we use case-insensitive, punctuation-insensitive matching
so "Runny Nose" and "runny nose" match; avoids false negatives from typing variation.
"""

import re


def normalize_symptom_text(text: str) -> str:
    """
    Normalize symptom text for comparison: lowercase, strip, collapse whitespace,
    remove punctuation. Returns empty string for non-string or empty input.
    """
    if not text or not isinstance(text, str):
        return ""
    cleaned = re.sub(r"[^\w\s]", "", text.lower())
    return " ".join(cleaned.split())
