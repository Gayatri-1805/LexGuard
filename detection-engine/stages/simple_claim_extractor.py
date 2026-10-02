"""
Simple Rule-Based Claim Extractor
==================================
A non-LLM alternative to claim_extractor.py for cases where:
1. Input text is already atomic (single claim per input)
2. You want to save API costs during testing
3. Claims are simple and don't need complex decomposition

Use this for:
- Testing with pre-decomposed claims
- Simple single-sentence inputs
- Batch processing where LLM cost is prohibitive

For complex multi-claim paragraphs, use the full LLM-based extractor.
"""
import re
from typing import Any
from shared.schemas import Claim, ClaimType


def extract_claims_simple(text: str) -> list[Claim]:
    """
    Extract claims using simple rule-based splitting (NO LLM calls).
    
    Logic:
    1. If text is a single sentence → return as single claim
    2. If text has multiple sentences → split by periods and create multiple claims
    3. Detect claim type based on keywords
    
    Args:
        text: Input text to extract claims from
        
    Returns:
        list[Claim] - one or more claims extracted from the text
    """
    if not text or not text.strip():
        return []
    
    # Split by sentence boundaries (simple heuristic)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
    
    if not sentences:
        # Fallback: treat entire text as single claim
        sentences = [text.strip()]
    
    claims = []
    for i, sentence in enumerate(sentences):
        # Detect claim type based on content
        sentence_lower = sentence.lower()
        
        if re.search(r'section\s+\d+[a-z]?', sentence_lower):
            claim_type = ClaimType.SECTION_REF
        elif any(word in sentence_lower for word in ['held', 'ruled', 'judgment', 'court', 'case']):
            claim_type = ClaimType.HOLDING
        elif any(word in sentence_lower for word in ['burden', 'proof', 'procedure', 'appeal', 'limitation']):
            claim_type = ClaimType.PROCEDURAL
        elif 'v.' in sentence or 'vs.' in sentence.lower():
            claim_type = ClaimType.CASE_CITATION
        else:
            claim_type = ClaimType.OTHER
        
        # Extract section reference if present
        section_match = re.search(r'(section\s+\d+[a-z]?)', sentence_lower)
        citation = section_match.group(1) if section_match else None
        
        claims.append(
            Claim(
                id=f"claim_{i+1}",
                text=sentence,
                type=claim_type,
                span=(0, len(sentence)),
                citation=citation,
                context=text  # Full original text as context
            )
        )
    
    return claims


def extract_claims_single(text: str, claim_id: str = "claim_1") -> list[Claim]:
    """
    Treat entire input as a single atomic claim (most efficient for test cases).
    
    Use this when:
    - Each test case is already a single claim
    - You're testing pre-decomposed claims
    - Maximum API efficiency is needed
    
    Args:
        text: Single claim text
        claim_id: Optional custom claim ID
        
    Returns:
        list[Claim] with exactly one claim
    """
    if not text or not text.strip():
        return []
    
    text = text.strip()
    text_lower = text.lower()
    
    # Detect claim type
    if re.search(r'section\s+\d+[a-z]?', text_lower):
        claim_type = ClaimType.SECTION_REF
    elif any(word in text_lower for word in ['held', 'ruled', 'judgment', 'court']):
        claim_type = ClaimType.HOLDING
    elif any(word in text_lower for word in ['burden', 'proof', 'procedure']):
        claim_type = ClaimType.PROCEDURAL
    elif 'v.' in text or 'vs.' in text_lower:
        claim_type = ClaimType.CASE_CITATION
    else:
        claim_type = ClaimType.OTHER
    
    # Extract section reference if present
    section_match = re.search(r'(section\s+\d+[a-z]?)', text_lower)
    citation = section_match.group(1) if section_match else None
    
    return [
        Claim(
            id=claim_id,
            text=text,
            type=claim_type,
            span=(0, len(text)),
            citation=citation,
            context=text
        )
    ]
