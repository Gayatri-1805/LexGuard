# Trust Score Calculation - Visual Diagrams

## 📊 **Complete Pipeline Flow**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT TEXT                                   │
│  "Section 67 punishes obscene material with 3 years imprisonment    │
│   and fine up to ten lakh rupees"                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 1: CLAIM EXTRACTION                         │
│                     (LLM-based decomposition)                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ├──► Claim 1: "Section 67 punishes obscene material"
                             ├──► Claim 2: "Punishment includes 3 years imprisonment"
                             └──► Claim 3: "Fine up to ten lakh rupees"
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 2: KB LOOKUP                                │
│              (Exact match + Semantic search)                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
             Claim 1│  Claim 2│  Claim 3
                    │        │        │
                    ▼        ▼        ▼
            ┌──────────┬──────────┬──────────┐
            │ Section  │ Section  │ Section  │
            │ 67 Text  │ 67 Text  │ 67 Text  │
            │ Score:   │ Score:   │ Score:   │
            │ 0.95 ✅  │ 0.95 ✅  │ 0.95 ✅  │
            │ KB Hit!  │ KB Hit!  │ KB Hit!  │
            └────┬─────┴────┬─────┴────┬─────┘
                 │          │          │
                 ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 3: VERDICT (LLM Judge)                      │
│                   (Compare claim vs KB evidence)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
                    ▼        ▼        ▼
            ┌──────────────────────────────────────┐
            │ Claim 1: SUPPORTED (1.0) ✅          │
            │ "Evidence supports obscene material" │
            ├──────────────────────────────────────┤
            │ Claim 2: SUPPORTED (1.0) ✅          │
            │ "3 years imprisonment confirmed"     │
            ├──────────────────────────────────────┤
            │ Claim 3: CONTRADICTED (0.0) ❌       │
            │ "Fine is 5 lakh, not 10 lakh"       │
            └─────────────┬────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 4: TRUST AGGREGATION                        │
│                      Trust = Σ(scores) / n                           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                   ┌─────────┴──────────┐
                   │  Scores: [1.0, 1.0, 0.0]
                   │  Trust = (1.0 + 1.0 + 0.0) / 3
                   │  Trust = 0.667
                   └─────────┬──────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    STAGE 5: DECISION LOGIC                           │
│                  (Pattern analysis + thresholds)                     │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                   ┌─────────┴──────────┐
                   │  contradiction_ratio = 1/3 = 0.33
                   │  support_ratio = 2/3 = 0.67
                   │  has_contradicted = True
                   │  has_supported = True
                   │  
                   │  Rule: "Mixed evidence with 
                   │         significant contradictions"
                   │  
                   │  Decision: ABSTAIN ⚠️
                   └─────────┬──────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FINAL RESPONSE                               │
│  {                                                                   │
│    "decision": "ABSTAIN",                                            │
│    "trust_index": 0.667,                                             │
│    "claims": 3,                                                      │
│    "verdicts": [                                                     │
│      {"label": "SUPPORTED", ...},                                    │
│      {"label": "SUPPORTED", ...},                                    │
│      {"label": "CONTRADICTED", ...}                                  │
│    ]                                                                 │
│  }                                                                   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Trust Score Calculation Detail**

```
┌─────────────────────────────────────────────────────────────┐
│            VERDICT LABEL → NUMERIC SCORE MAPPING             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  SUPPORTED          ──────────► 1.0  ✅ (Strong evidence)   │
│  ENTAILED           ──────────► 1.0  ✅ (Logically follows) │
│  PARTIALLY_SUPPORTED ─────────► 0.5  ⚠️  (Partial match)    │
│  UNVERIFIABLE       ──────────► 0.5  ❓ (No evidence)       │
│  NOT_ENOUGH_INFO    ──────────► 0.5  ❓ (Insufficient)      │
│  CONTRADICTED       ──────────► 0.0  ❌ (Evidence opposes)  │
│  LOW_RISK_SKIP      ──────────► None 🔇 (Excluded)          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  AGGREGATE CALCULATION                       │
│                                                              │
│  Example: 3 verdicts                                         │
│    • Verdict 1: SUPPORTED (1.0)                              │
│    • Verdict 2: PARTIALLY_SUPPORTED (0.5)                    │
│    • Verdict 3: CONTRADICTED (0.0)                           │
│                                                              │
│  Trust = (1.0 + 0.5 + 0.0) / 3 = 1.5 / 3 = 0.500            │
│                                                              │
│  ┌──────────────────────────────────────────┐               │
│  │ Trust Score: 0.500 (Medium Trust) ⚠️     │               │
│  └──────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚦 **Decision Logic Flowchart**

```
                         START
                           │
                           ▼
              ┌────────────────────────┐
              │ Calculate Metrics:     │
              │ • trust                │
              │ • contradiction_ratio  │
              │ • support_ratio        │
              │ • has_contradicted     │
              │ • has_supported        │
              │ • has_partial          │
              └────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │ contradiction_ratio >= 0.4?  │────YES────► FLAGGED ❌
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ Only CONTRADICTED,           │
        │ no SUPPORTED?                │────YES────► FLAGGED ❌
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ Mixed evidence AND           │
        │ contradiction_ratio >= 0.2?  │────YES────► ABSTAIN ⚠️
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ support_ratio >= 0.6 AND     │
        │ no contradictions?           │────YES────► SAFE ✅
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ Has SUPPORTED AND            │
        │ trust >= 0.75 AND            │
        │ no contradictions?           │────YES────► SAFE ✅
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ Has PARTIAL AND              │
        │ no contradictions?           │────YES────► ABSTAIN ⚠️
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ Mixed: both CONTRADICTED     │
        │ and SUPPORTED?               │────YES────► ABSTAIN ⚠️
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ trust >= 0.8?                │────YES────► SAFE ✅
        └──────────┬───────────────────┘
                   │ NO
                   ▼
        ┌──────────────────────────────┐
        │ trust <= 0.3?                │────YES────► FLAGGED ❌
        └──────────┬───────────────────┘
                   │ NO
                   ▼
                ABSTAIN ⚠️
              (Uncertain)
```

---

## 📊 **Trust Score Distribution Examples**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PERFECT ACCURACY (Trust = 1.0)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Claims: 3                                                           │
│  ┌────────────┬────────────┬────────────┐                           │
│  │ SUPPORTED  │ SUPPORTED  │ SUPPORTED  │                           │
│  │   (1.0)    │   (1.0)    │   (1.0)    │                           │
│  └────────────┴────────────┴────────────┘                           │
│                                                                      │
│  Trust = (1.0 + 1.0 + 1.0) / 3 = 1.000 ✅                           │
│  Decision: SAFE (All evidence supports claims)                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              COMPLETE HALLUCINATION (Trust = 0.0)                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Claims: 2                                                           │
│  ┌────────────┬────────────┐                                        │
│  │CONTRADICTED│CONTRADICTED│                                        │
│  │   (0.0)    │   (0.0)    │                                        │
│  └────────────┴────────────┘                                        │
│                                                                      │
│  Trust = (0.0 + 0.0) / 2 = 0.000 ❌                                 │
│  Decision: FLAGGED (All claims contradicted)                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│            PARTIAL HALLUCINATION (Trust = 0.5-0.7)                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Claims: 4                                                           │
│  ┌────────────┬────────────┬────────────┬────────────┐              │
│  │ SUPPORTED  │ SUPPORTED  │CONTRADICTED│ PARTIAL    │              │
│  │   (1.0)    │   (1.0)    │   (0.0)    │   (0.5)    │              │
│  └────────────┴────────────┴────────────┴────────────┘              │
│                                                                      │
│  Trust = (1.0 + 1.0 + 0.0 + 0.5) / 4 = 0.625 ⚠️                     │
│  Decision: ABSTAIN (Mixed evidence, significant contradiction)      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                UNVERIFIABLE (Trust = 0.5)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Claims: 2                                                           │
│  ┌────────────┬────────────┐                                        │
│  │UNVERIFIABLE│UNVERIFIABLE│                                        │
│  │   (0.5)    │   (0.5)    │                                        │
│  └────────────┴────────────┘                                        │
│                                                                      │
│  Trust = (0.5 + 0.5) / 2 = 0.500 ❓                                 │
│  Decision: ABSTAIN (Cannot verify claims)                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📈 **Trust Score Spectrum**

```
  0.0                  0.5                  1.0
   │────────────────────│────────────────────│
   │                    │                    │
   ▼                    ▼                    ▼
FLAGGED              ABSTAIN               SAFE
   ❌                   ⚠️                   ✅

├──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┤
│ 0.0  │ 0.1  │ 0.2  │ 0.3  │ 0.4  │ 0.5  │ 0.6  │ 0.7  │ 0.8  │ 0.9  │ 1.0
├──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┤
│                                                                       │
│  ◄────── Very Low ──────►  ◄──── Low ────► ◄── Medium ──► ◄── High ──►
│                                                                       │
│  Complete              Significant     Mixed       Mostly    Perfect  │
│  Hallucination         Hallucination   Evidence   Accurate  Accuracy  │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

Thresholds:
  • trust <= 0.3  → Automatic FLAGGED
  • trust >= 0.8  → Automatic SAFE  
  • 0.3 < trust < 0.8 → Pattern analysis
```

---

## 🔍 **Contradiction Ratio Impact**

```
┌─────────────────────────────────────────────────────────────────────┐
│          EFFECT OF CONTRADICTION RATIO ON DECISION                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Scenario 1: High Contradiction (≥40%)                               │
│  ┌──────────────────────────────────────────────────┐               │
│  │ 10 Claims: 6 CONTRADICTED, 4 SUPPORTED           │               │
│  │ contradiction_ratio = 6/10 = 0.6 (60%)           │               │
│  │ trust = (6×0.0 + 4×1.0)/10 = 0.4                 │               │
│  │                                                   │               │
│  │ Result: FLAGGED ❌ (High contradiction)          │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
│  Scenario 2: Significant Contradiction (≥20%, mixed)                 │
│  ┌──────────────────────────────────────────────────┐               │
│  │ 10 Claims: 2 CONTRADICTED, 8 SUPPORTED           │               │
│  │ contradiction_ratio = 2/10 = 0.2 (20%)           │               │
│  │ trust = (2×0.0 + 8×1.0)/10 = 0.8                 │               │
│  │ has_contradicted = True, has_supported = True    │               │
│  │                                                   │               │
│  │ Result: ABSTAIN ⚠️ (Mixed evidence)              │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
│  Scenario 3: Low Contradiction (<20%)                                │
│  ┌──────────────────────────────────────────────────┐               │
│  │ 10 Claims: 1 CONTRADICTED, 9 SUPPORTED           │               │
│  │ contradiction_ratio = 1/10 = 0.1 (10%)           │               │
│  │ trust = (1×0.0 + 9×1.0)/10 = 0.9                 │               │
│  │ has_supported = True, trust >= 0.75              │               │
│  │                                                   │               │
│  │ Result: Depends on other rules (likely SAFE ✅)  │               │
│  └──────────────────────────────────────────────────┘               │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 **Key Takeaways**

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TRUST SCORE ESSENTIALS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1️⃣  Trust = Average of verdict scores (0.0 to 1.0)                │
│      Simple, interpretable, transparent                             │
│                                                                      │
│  2️⃣  Verdicts map to scores:                                        │
│      • SUPPORTED/ENTAILED → 1.0 ✅                                  │
│      • CONTRADICTED → 0.0 ❌                                        │
│      • PARTIAL/UNVERIFIABLE → 0.5 ⚠️                                │
│                                                                      │
│  3️⃣  Decision uses pattern analysis, not just trust:                │
│      • Contradiction ratio                                          │
│      • Support ratio                                                │
│      • Verdict combinations                                         │
│                                                                      │
│  4️⃣  Conservative approach:                                         │
│      • Prefer ABSTAIN over risky SAFE/FLAGGED                       │
│      • Any significant contradiction triggers caution               │
│                                                                      │
│  5️⃣  Tunable thresholds:                                            │
│      • Can adjust based on domain/use case                          │
│      • Currently optimized for legal accuracy                       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

**For detailed explanation, see:** `TRUST_SCORE_METHODOLOGY.md`  
**For implementation, see:** `api-and-sdk/api/routes/check.py`
