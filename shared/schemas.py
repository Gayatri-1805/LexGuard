"""
Pydantic v2 shared data models for legal-domain LLM hallucination detection.

This file defines the contract for the three-service architecture:
  - detection-engine (Person A): produces Claim, Verdict, CheckResponse
  - api-and-sdk (Person B): accepts CheckRequest, returns CheckResponse
  - dashboard-and-eval (Person C): queries verdicts, analyzes trust_index and Decision

Data flow:
  1. Person B receives CheckRequest (user's LLM output to check)
  2. Person B calls Person A's pipeline
  3. Person A decomposes → stages 0-4 → produces list[Verdict]
  4. Person A returns CheckResponse with claims, verdicts, trust_index, decision
  5. Person B persists to analytics DB, returns to client
  6. Person C queries analytics DB, visualizes decision distribution and confidence

All models are immutable (frozen=True) to represent completed analysis steps.
No business logic here — pure data contracts only.
"""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ClaimType(str, Enum):
    """Types of legal claims that can be extracted (Stage 0: Decompose)."""
    CASE_CITATION = "CASE_CITATION"      # e.g., "Miranda v. Arizona (1966)"
    SECTION_REF = "SECTION_REF"          # e.g., "42 U.S.C. § 1983"
    HOLDING = "HOLDING"                  # e.g., "The court ruled that..."
    PROCEDURAL = "PROCEDURAL"            # e.g., "The burden of proof is..."
    OTHER = "OTHER"                      # Unclassified legal claim


class Claim(BaseModel):
    """
    An atomic legal claim extracted from LLM output (Stage 0: Decompose).

    Produced by: detection-engine/stages/stage0_decompose.py
    Consumed by: detection-engine/pipeline.py (stages 1-4), analytics-db/models.py

    Immutable to represent a completed decomposition.
    """
    model_config = ConfigDict(frozen=True)

    id: str = Field(
        ...,
        description="Unique identifier for this claim within a CheckResponse. "
                    "Typically a short numeric string or UUID fragment."
    )
    text: str = Field(
        ...,
        description="The atomic legal claim text, as decomposed from the original LLM output. "
                    "E.g., 'Miranda v. Arizona requires police to read suspects their rights.'"
    )
    type: ClaimType = Field(
        default=ClaimType.OTHER,
        description="Classification of the claim type for downstream routing and grounding."
    )
    span: tuple[int, int] = Field(
        ...,
        description="Character offsets (start, end) in the original LLM output where this claim appears. "
                    "Used for tracing back to source text. E.g., (120, 180)."
    )


class VerdictLabel(str, Enum):
    """Outcome of the hallucination detection pipeline (Stages 1-4)."""
    ENTAILED = "ENTAILED"                  # Claim is supported by retrieved evidence
    CONTRADICTED = "CONTRADICTED"          # Claim is refuted by retrieved evidence
    NOT_ENOUGH_INFO = "NOT_ENOUGH_INFO"    # Insufficient evidence to decide
    LOW_RISK_SKIP = "LOW_RISK_SKIP"        # Stage 1 filtered out as non-falsifiable


class Verdict(BaseModel):
    """
    The hallucination detection result for a single claim (Stages 1-4 output).

    Produced by: detection-engine/stages/stage1_filter.py through stage4_trust_score.py
    Consumed by: api-and-sdk/routes/check.py (returned in CheckResponse),
                 analytics-db/models.py (persisted), eval/scoring.py (evaluated)

    Immutable to represent a completed analysis for this claim.
    """
    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(
        ...,
        description="Foreign key reference to Claim.id. Links this verdict to the claim analyzed."
    )
    label: VerdictLabel = Field(
        ...,
        description="The hallucination classification: whether the claim is entailed, contradicted, "
                    "lacks evidence, or was skipped as non-falsifiable."
    )
    evidence: list[str] = Field(
        default_factory=list,
        description="Retrieved passages or knowledge base text that support this verdict. "
                    "Empty list if label is LOW_RISK_SKIP or NOT_ENOUGH_INFO. "
                    "E.g., ['42 U.S.C. § 1983 provides a civil cause of action...', "
                    "'In Miranda v. Arizona, the Court held...']"
    )
    stage_reached: int = Field(
        ...,
        ge=1, le=4,
        description="Pipeline stage that produced this verdict (1=Filter, 2=Ground, 3=Metamorphic, 4=Trust Score). "
                    "Used to understand at which point the analysis terminated."
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0, le=1.0,
        description="Confidence score (0-1) of the verdict, if produced by the stage. "
                    "None if the stage does not compute a confidence. "
                    "Stage 4 always populates this; earlier stages may."
    )


class Decision(str, Enum):
    """Final decision from the pipeline (Stage 4: Trust Score)."""
    SAFE = "SAFE"              # Majority of claims entailed or low-risk; trust_index high
    FLAGGED = "FLAGGED"        # Hallucinations detected; trust_index low
    ABSTAIN = "ABSTAIN"        # Insufficient evidence to make a decision


class CheckRequest(BaseModel):
    """
    Input to the hallucination detection pipeline (from Person B's API).

    Produced by: api-and-sdk/routes/check.py (receives from client)
    Consumed by: detection-engine/pipeline.py

    Mutable (not frozen) because it's a request input, not a completed analysis.
    """
    text: str = Field(
        ...,
        description="The LLM-generated output text to check for hallucinations. "
                    "E.g., a legal summary, case analysis, or regulation explanation."
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional context or system prompt that produced the text. "
                    "Useful for debugging or understanding the LLM's framing. "
                    "May be ignored by the pipeline."
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Optional caller-supplied unique identifier for tracing. "
                    "If not provided, CheckResponse.request_id will be generated."
    )


class CheckResponse(BaseModel):
    """
    Output from the hallucination detection pipeline (Person A produces, Person B returns).

    Produced by: detection-engine/pipeline.py
    Consumed by: api-and-sdk/routes/check.py (returned to client),
                 analytics-db/models.py (persisted for dashboard),
                 dashboard-and-eval/eval/scoring.py (evaluated against gold set)

    Immutable to represent a completed analysis snapshot.
    """
    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "example": {
                "request_id": "req-550e8400-e29b-41d4-a716-446655440000",
                "claims": [
                    {
                        "id": "claim_001",
                        "text": "42 U.S.C. Section 1983 requires law enforcement to obtain a warrant before entering a home.",
                        "type": "SECTION_REF",
                        "span": (0, 102)
                    },
                    {
                        "id": "claim_002",
                        "text": "Warrants based on anonymous tips are always invalid.",
                        "type": "HOLDING",
                        "span": (103, 162)
                    }
                ],
                "verdicts": [
                    {
                        "claim_id": "claim_001",
                        "label": "CONTRADICTED",
                        "evidence": [
                            "42 U.S.C. § 1983 provides a civil cause of action for deprivation of rights, "
                            "not procedural requirements for warrants.",
                            "The warrant requirement is grounded in the Fourth Amendment, not § 1983."
                        ],
                        "stage_reached": 2,
                        "confidence": 0.95
                    },
                    {
                        "claim_id": "claim_002",
                        "label": "CONTRADICTED",
                        "evidence": [
                            "Alabama v. White, 496 U.S. 325 (1990): Anonymous tips may provide reasonable suspicion, "
                            "sufficient for a traffic stop."
                        ],
                        "stage_reached": 2,
                        "confidence": 0.92
                    }
                ],
                "trust_index": 0.18,
                "decision": "FLAGGED",
                "created_at": "2026-09-04T15:30:45.123456+00:00"
            }
        }
    )

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for this analysis request. "
                    "Generated server-side if not supplied in CheckRequest.request_id. "
                    "Used for tracing across logs and analytics."
    )
    claims: list[Claim] = Field(
        ...,
        description="List of atomic claims extracted from the input text (Stage 0 output). "
                    "Empty list if the input text contained no falsifiable claims."
    )
    verdicts: list[Verdict] = Field(
        ...,
        description="List of verdicts, one per claim (or fewer if early stages skipped claims). "
                    "Verdict order should match claim order when possible."
    )
    trust_index: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="Aggregate hallucination risk score (0-1) from Stage 4: Trust Score. "
                    "0 = high hallucination risk, 1 = low hallucination risk (trustworthy). "
                    "Computed from weighted evidence across all verdicts."
    )
    decision: Decision = Field(
        ...,
        description="Final decision from Stage 4: SAFE (trust_index high), "
                    "FLAGGED (detected hallucinations), or ABSTAIN (insufficient evidence)."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the analysis was completed (UTC). "
                    "Useful for dashboard sorting and temporal analysis."
    )
