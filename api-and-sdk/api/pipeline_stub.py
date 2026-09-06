"""
Stub pipeline for testing before Person A completes detection-engine/pipeline.py.

Returns a realistic CheckResponse shape using the json_schema_extra example from shared/schemas.py.
This lets Person B build the API and Person C build the dashboard without blocking on Person A.

IMPORTANT: Replace with real pipeline by changing the import:
  OLD: from api.pipeline_stub import check as PIPELINE_CHECK_FN
  NEW: from detection_engine.pipeline import check as PIPELINE_CHECK_FN
"""

import sys
from pathlib import Path
from uuid import uuid4

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.schemas import (
    CheckResponse, Claim, ClaimType, Verdict, VerdictLabel, Decision
)


def check(text: str, context: str | None = None) -> CheckResponse:
    """
    Stub pipeline that returns a realistic CheckResponse for testing.

    Args:
        text: LLM output to check
        context: Optional context/prompt that produced the text

    Returns:
        CheckResponse with realistic example claims, verdicts, trust_index, decision
    """
    # Parse the input text for demo purposes (simplified)
    # Detect hallucination keywords
    hallucination_keywords = [
        "only applies to government", "no liability", "forbids data protection",
        "all data breaches are legal", "not protected", "no restrictions",
        "invalid under", "never required", "completely false", "gross negligence"
    ]
    
    # Detect text length to vary verdict distribution
    text_length = len(text)
    hallucination_score = sum(1 for keyword in hallucination_keywords if keyword in text.lower())
    
    contains_hallucination = hallucination_score >= 2  # Need at least 2 hallucination keywords
    contains_section = "section" in text.lower() or "43" in text or "section 43a" in text.lower()
    contains_case = "case" in text.lower() or "miranda" in text.lower() or "warrant" in text.lower()
    contains_procedural = "burden" in text.lower() or "proof" in text.lower()

    claims = []
    verdicts = []
    
    # Determine how many claims to generate based on text length
    # Lower threshold: 50 chars → 1 claim, 80 chars → 2 claims, 150+ chars → 3 claims
    if text_length < 70:
        num_claims = 1
    elif text_length < 130:
        num_claims = 2
    else:
        num_claims = 3

    # Demo claim 1: Section reference
    if contains_section or len(text) > 50:
        claims.append(
            Claim(
                id="claim_001",
                text="Section 43A of the IT Act requires data protection measures.",
                type=ClaimType.SECTION_REF,
                span=(0, 60),
            )
        )
        
        # Verdict depends on hallucination detection
        if contains_hallucination:
            verdicts.append(
                Verdict(
                    claim_id="claim_001",
                    label=VerdictLabel.CONTRADICTED,
                    evidence=[
                        "Section 43A: Compensation for failure to protect data. "
                        "Where a person (including a body corporate) causes loss or damage..."
                    ],
                    stage_reached=2,
                    confidence=0.95,
                )
            )
        else:
            verdicts.append(
                Verdict(
                    claim_id="claim_001",
                    label=VerdictLabel.ENTAILED,
                    evidence=[
                        "Section 43A: Compensation for failure to protect data. "
                        "Where a person (including a body corporate) causes loss or damage..."
                    ],
                    stage_reached=2,
                    confidence=0.92,
                )
            )

    # Demo claim 2: Case citation / Privacy rights
    if (contains_case or len(text) > 100) and num_claims >= 2:
        claims.append(
            Claim(
                id="claim_002",
                text="Privacy is a fundamental right under the Constitution.",
                type=ClaimType.HOLDING,
                span=(61, 120),
            )
        )
        
        if contains_hallucination:
            verdicts.append(
                Verdict(
                    claim_id="claim_002",
                    label=VerdictLabel.CONTRADICTED,
                    evidence=[
                        "K.S. Puttaswamy v. Union of India (2017) 10 SCC 1: "
                        "Privacy is a fundamental right protected by Articles 14, 19, and 21."
                    ],
                    stage_reached=2,
                    confidence=0.93,
                )
            )
        else:
            verdicts.append(
                Verdict(
                    claim_id="claim_002",
                    label=VerdictLabel.ENTAILED,
                    evidence=[
                        "K.S. Puttaswamy v. Union of India (2017) 10 SCC 1: "
                        "Privacy is a fundamental right protected by Articles 14, 19, and 21."
                    ],
                    stage_reached=2,
                    confidence=0.88,
                )
            )

    # Demo claim 3: Procedural (often contradicted to create mixed verdicts)
    # Generate for 2+ claims (not just 3) so we get ABSTAIN with mixed verdicts
    if (contains_procedural or len(text) > 80) and num_claims >= 2:
        claims.append(
            Claim(
                id="claim_003",
                text="Data breach victims must prove willful negligence.",
                type=ClaimType.PROCEDURAL,
                span=(121, 180),
            )
        )
        
        # Claim 3 is always contradicted to create mixed verdicts
        verdicts.append(
            Verdict(
                claim_id="claim_003",
                label=VerdictLabel.CONTRADICTED,
                evidence=[
                    "Section 43A imposes strict liability for failure to protect data. "
                    "Willfulness or negligence is not required."
                ],
                stage_reached=2,
                confidence=0.85,
            )
        )

    # Compute trust_index and decision based on verdicts
    if not verdicts:
        # No falsifiable claims detected
        trust_index = 0.95
        decision = Decision.SAFE
    else:
        # Count verdicts by label
        entailed_count = sum(1 for v in verdicts if v.label == VerdictLabel.ENTAILED)
        contradicted_count = sum(1 for v in verdicts if v.label == VerdictLabel.CONTRADICTED)
        not_enough_count = sum(1 for v in verdicts if v.label == VerdictLabel.NOT_ENOUGH_INFO)
        total_count = len(verdicts)

        # Improved heuristic: trust_index = (entailed + 0.5*not_enough) / total
        trust_index = (entailed_count + 0.5 * not_enough_count) / total_count
        trust_index = max(0.0, min(1.0, trust_index))

        # Decision based on verdict distribution
        if contradicted_count > 0:
            # If any claims are contradicted, it's a hallucination
            if contradicted_count >= entailed_count:
                decision = Decision.FLAGGED
            elif trust_index >= 0.75:
                decision = Decision.SAFE
            else:
                decision = Decision.ABSTAIN
        elif trust_index >= 0.75:
            decision = Decision.SAFE
        else:
            decision = Decision.ABSTAIN

    return CheckResponse(
        request_id=str(uuid4()),
        claims=claims,
        verdicts=verdicts,
        trust_index=trust_index,
        decision=decision,
    )
