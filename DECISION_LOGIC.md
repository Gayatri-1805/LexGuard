# Decision Logic: How FLAGGED/ABSTAIN/SAFE Are Determined (Person B)

## Overview

As **Person B (API Developer)**, you are responsible for implementing **Stage 4: Trust Score → Decision** that converts the pipeline's verdict data into a final `FLAGGED`, `ABSTAIN`, or `SAFE` decision.

The current implementation in `api-and-sdk/api/pipeline_stub.py` shows how this works:

---

## Stage 4: Decision Algorithm

```
Input: claims[], verdicts[] from Stages 0-3
       ↓
       Count verdicts by label:
         - entailed_count = # of ENTAILED verdicts
         - contradicted_count = # of CONTRADICTED verdicts  
         - not_enough_count = # of NOT_ENOUGH_INFO verdicts
       ↓
       Compute trust_index = (entailed + 0.5 * not_enough) / total
                            (range: 0.0 to 1.0)
       ↓
       Apply decision thresholds → FLAGGED / ABSTAIN / SAFE
Output: decision (enum), trust_index (float)
```

---

## Decision Tree (Current Implementation)

```
START
  │
  ├─ No verdicts generated?
  │  └─→ trust_index = 0.95
  │      decision = SAFE ✓
  │
  └─ Verdicts exist
     │
     ├─ contradicted_count > 0 (hallucinations detected)
     │  │
     │  ├─ contradicted_count >= entailed_count?
     │  │  └─→ decision = FLAGGED 🚩
     │  │      (More hallucinations than valid claims)
     │  │      trust_index = (entailed + 0.5*not_enough) / total
     │  │      Example: 3 CONTRADICTED, 0 ENTAILED → trust_index = 0.0 → FLAGGED
     │  │
     │  ├─ trust_index >= 0.75?
     │  │  └─→ decision = SAFE ✓
     │  │      (Mostly valid, few contradictions)
     │  │      Example: 2 ENTAILED, 1 CONTRADICTED → trust_index = 0.67 → NOT >= 0.75 → skip
     │  │
     │  └─ else
     │     └─→ decision = ABSTAIN ⚠️
     │         (Mixed signals, unclear)
     │         Example: 2 ENTAILED, 1 CONTRADICTED → trust_index = 0.67 → ABSTAIN
     │
     └─ contradicted_count == 0 (no hallucinations)
        │
        ├─ trust_index >= 0.75?
        │  └─→ decision = SAFE ✓
        │
        └─ else
           └─→ decision = ABSTAIN ⚠️
```

---

## Examples with Actual Data

### Example 1: FLAGGED ✅

**Input text:** "Section 43A only applies to government agencies. No liability whatsoever. Constitution forbids data protection."

**Verdicts generated:**
```
claim_001: CONTRADICTED (confidence: 0.95)
claim_002: CONTRADICTED (confidence: 0.93)
claim_003: CONTRADICTED (confidence: 0.85)
```

**Decision Calculation:**
```
entailed_count = 0
contradicted_count = 3
not_enough_count = 0
total_count = 3

trust_index = (0 + 0.5*0) / 3 = 0.0
contradicted_count (3) >= entailed_count (0)? YES
→ decision = FLAGGED 🚩
→ trust_index = 0.0
```

---

### Example 2: ABSTAIN ⚠️

**Input text:** "Data breach victims must prove willful negligence under Section 43A. Privacy is a fundamental right."

**Verdicts generated:**
```
claim_001: ENTAILED (confidence: 0.92)
claim_002: ENTAILED (confidence: 0.88)
claim_003: CONTRADICTED (confidence: 0.85)
```

**Decision Calculation:**
```
entailed_count = 2
contradicted_count = 1
not_enough_count = 0
total_count = 3

trust_index = (2 + 0.5*0) / 3 = 0.67
contradicted_count (1) > 0? YES
contradicted_count (1) >= entailed_count (2)? NO
trust_index (0.67) >= 0.75? NO
→ decision = ABSTAIN ⚠️
→ trust_index = 0.67
```

---

### Example 3: SAFE ✓

**Input text:** "Section 43A requires data protection measures."

**Verdicts generated:**
```
claim_001: ENTAILED (confidence: 0.92)
```

**Decision Calculation:**
```
entailed_count = 1
contradicted_count = 0
not_enough_count = 0
total_count = 1

trust_index = (1 + 0.5*0) / 1 = 1.0
contradicted_count (0) > 0? NO
trust_index (1.0) >= 0.75? YES
→ decision = SAFE ✓
→ trust_index = 1.0
```

---

## Key Decision Thresholds

| Threshold | Meaning | Used When |
|-----------|---------|-----------|
| `contradicted_count >= entailed_count` | Majority are hallucinations | Determine FLAGGED |
| `trust_index >= 0.75` | High confidence in correctness | Determine SAFE vs ABSTAIN |
| `contradicted_count > 0` | Any hallucinations detected | Trigger detailed analysis |

---

## How Person A Influences These Decisions

**Person A (detection-engine)** produces the **verdicts** array by:

1. **Stage 0 (Decompose):** Extracts claims from LLM output
2. **Stage 1 (Filter):** Removes low-risk claims (no `CONTRADICTED` here)
3. **Stage 2 (Retrieve + NLI):** Grounds each claim in KB, produces `ENTAILED` or `CONTRADICTED` verdicts
4. **Stage 3 (Metamorphic):** Refines verdicts with consistency checks
5. **Stage 4 (Confidence):** Adds confidence scores

**Person B (you)** then:
- Counts the verdicts by label
- Applies the decision algorithm
- Returns `FLAGGED`, `ABSTAIN`, or `SAFE` to the SDK

---

## Integration Point: Swapping Person A's Pipeline

Currently, the stub is in `api-and-sdk/api/pipeline_stub.py`. To integrate Person A's real pipeline:

**File:** `api-and-sdk/api/routes/check.py`

```python
# CURRENT (stub):
from api.pipeline_stub import check as PIPELINE_CHECK_FN

# CHANGE TO (when Person A is ready):
from detection_engine.pipeline import check as PIPELINE_CHECK_FN
```

Person A's pipeline must return a `CheckResponse` object with:
- `claims: list[Claim]`
- `verdicts: list[Verdict]`  ← Person B counts these
- `trust_index: float`        ← Person B computes this
- `decision: Decision`         ← Person B determines this

---

## Summary: Person B's Responsibilities

```
┌─────────────────────────────────────────┐
│ Person B: Stage 4 Implementation        │
├─────────────────────────────────────────┤
│                                         │
│ 1. Receive verdicts from Person A       │
│ 2. Count ENTAILED vs CONTRADICTED       │
│ 3. Compute trust_index formula          │
│ 4. Apply decision thresholds            │
│ 5. Return FLAGGED / ABSTAIN / SAFE      │
│ 6. Log to Analytics DB (Person C uses)  │
│                                         │
└─────────────────────────────────────────┘
```

You are implementing **Stage 4: Trust Score → Decision**, which is the final stage of the hallucination detection pipeline before returning to the SDK and logging to analytics.
