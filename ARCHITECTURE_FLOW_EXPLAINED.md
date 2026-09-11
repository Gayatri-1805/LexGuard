# LexGuard Architecture: KB + LLM Judge Flow Explained

**Question:** If it's in the KB, does LLM as a judge still happen? Which models are used?

---

## 🎯 Quick Answer

**YES, LLM judge ALWAYS runs**, even when KB has the data. Here's why:

1. **KB provides EVIDENCE** (statute text)
2. **LLM judge VERIFIES** the claim against that evidence
3. This is the core innovation: **KB retrieval + LLM verification**

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER REQUEST                                 │
│  "Section 43A requires imprisonment for data breach"            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 0: CLAIM DECOMPOSITION (LLM #1)                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Model: Groq openai/gpt-oss-120b                                │
│  Input: Raw text                                                │
│  Output: [                                                      │
│    {                                                            │
│      "text": "Section 43A requires imprisonment",              │
│      "type": "SECTION_REF",                                    │
│      "citation": "Section 43A"                                 │
│    }                                                            │
│  ]                                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: KB LOOKUP (No LLM)                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Two parallel searches:                                         │
│                                                                 │
│  1. EXACT MATCH (PostgreSQL):                                  │
│     Query: SELECT text FROM statute_sections                   │
│            WHERE section_number = '43A'                         │
│            AND act_name = 'IT Act'                             │
│     Result: "Section 43A... compensation for failure to        │
│              protect data..." (found!)                         │
│                                                                 │
│  2. SEMANTIC SEARCH (FAISS):                                   │
│     Query embedding: embed("Section 43A imprisonment")         │
│     Search: Find top 3 most similar statute embeddings         │
│     Result: [                                                  │
│       {score: 0.89, text: "Section 43A..."},                   │
│       {score: 0.72, text: "Section 43..."},                    │
│       {score: 0.65, text: "Section 66..."}                     │
│     ]                                                           │
│                                                                 │
│  KB provides EVIDENCE, not verdict!                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: LLM JUDGE (LLM #2)                                    │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Model: Groq openai/gpt-oss-120b (SAME MODEL)                  │
│                                                                 │
│  Prompt:                                                        │
│    "You are a legal citation verifier.                         │
│     Claim: 'Section 43A requires imprisonment'                 │
│     Evidence: 'Section 43A... compensation for failure...'"    │
│     Does the evidence support the claim?                       │
│                                                                 │
│  LLM Reasoning:                                                 │
│    "The evidence mentions 'compensation' (civil liability)     │
│     but the claim states 'imprisonment' (criminal penalty).    │
│     These are contradictory."                                  │
│                                                                 │
│  Output: {                                                      │
│    "verdict": "CONTRADICTED",                                  │
│    "confidence": 0.96,                                         │
│    "reasoning": "Section 43A is civil, not criminal..."        │
│  }                                                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: TRUST SCORE AGGREGATION (No LLM)                      │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  Aggregate all verdicts:                                        │
│    - SUPPORTED: weight 1.0                                     │
│    - CONTRADICTED: weight 0.0                                  │
│    - PARTIALLY_SUPPORTED: weight 0.5                           │
│    - UNVERIFIABLE: weight 0.5                                  │
│                                                                 │
│  Trust Index = weighted_sum / total_claims                     │
│              = 0.0 / 1 = 0.0                                   │
│                                                                 │
│  Decision:                                                      │
│    if trust_index < 0.5 → FLAGGED                             │
│    if trust_index > 0.8 → SAFE                                │
│    else → ABSTAIN                                              │
│                                                                 │
│  Result: FLAGGED (trust_index = 0.0)                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  FINAL RESPONSE                                                 │
│  {                                                              │
│    "decision": "FLAGGED",                                       │
│    "trust_index": 0.0,                                         │
│    "claims": [...],                                            │
│    "verdicts": [                                               │
│      {                                                          │
│        "label": "CONTRADICTED",                                │
│        "evidence": ["Section 43A... compensation..."],         │
│        "confidence": 0.96,                                     │
│        "reasoning": "..."                                       │
│      }                                                          │
│    ]                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔍 Detailed Flow Analysis

### When Claim is in KB:

```
Scenario: User claims "Section 43A provides compensation"

1. ✅ KB Lookup SUCCEEDS
   - PostgreSQL: Finds Section 43A text
   - FAISS: Finds similar sections with high similarity
   
2. ✅ LLM Judge STILL RUNS
   - Gets the KB evidence
   - Compares claim text vs evidence text
   - Returns: SUPPORTED (because they match)
   
3. ✅ Result: SAFE (trust_index = 1.0)
```

### When Claim is NOT in KB:

```
Scenario: User claims "Section 999Z criminalizes AI deepfakes"

1. ❌ KB Lookup FAILS
   - PostgreSQL: Section 999Z not found
   - FAISS: No similar sections above threshold
   
2. ⚠️ LLM Judge CANNOT RUN
   - No evidence to verify against
   - Cannot make verdict without KB data
   
3. ⚠️ Result: UNVERIFIABLE → ABSTAIN (trust_index = 0.5)
```

### When Claim CONTRADICTS KB:

```
Scenario: User claims "Section 43A requires imprisonment"

1. ✅ KB Lookup SUCCEEDS
   - Finds: "Section 43A... compensation..." (civil)
   
2. ✅ LLM Judge DETECTS CONTRADICTION
   - Evidence says: "compensation" (civil)
   - Claim says: "imprisonment" (criminal)
   - Returns: CONTRADICTED
   
3. 🚨 Result: FLAGGED (trust_index = 0.0)
```

---

## 🤖 Which Models Are Used?

### Current Configuration (from .env):

```bash
# LLM for BOTH claim extraction AND judging
JUDGE_MODEL=openai/gpt-oss-120b
OPENAI_API_KEY=gsk_**** # Your Groq API key
OPENAI_BASE_URL=https://api.groq.com/openai/v1
```

### Model Usage:

| Task | Model | Provider | Purpose |
|------|-------|----------|---------|
| **Claim Decomposition** | `openai/gpt-oss-120b` | Groq | Break text into atomic claims |
| **LLM Judge** | `openai/gpt-oss-120b` | Groq | Verify claims against KB evidence |
| **Embeddings** | `all-MiniLM-L6-v2` | Local (sentence-transformers) | Create vectors for FAISS search |

### Why Same Model for Both Tasks?

- **Consistency:** Same reasoning quality
- **Cost efficiency:** One API provider
- **Simplicity:** One configuration

### Model Details:

**Groq openai/gpt-oss-120b:**
- **Type:** Open-source LLM via Groq
- **Size:** 120 billion parameters
- **Speed:** Very fast (Groq's LPU infrastructure)
- **Cost:** Free tier (200k tokens/day)
- **Use case:** Both extraction and judging

**all-MiniLM-L6-v2:**
- **Type:** Sentence embedding model
- **Size:** ~80MB
- **Dimensions:** 384
- **Speed:** Local, very fast
- **Cost:** Free (runs locally)
- **Use case:** Convert text to vectors for FAISS

---

## 📊 KB vs LLM Interaction

### The KB's Role:

```
KB = Knowledge Base (Ground Truth Repository)

What it contains:
  ✓ 115 IT Act statute sections
  ✓ 12 case law entries  
  ✓ 123 total FAISS embeddings
  
What it does:
  ✓ Provides EVIDENCE (statute text)
  ✓ Enables semantic search (find relevant sections)
  ✓ Enables exact lookup (get Section 43A)
  
What it DOES NOT do:
  ✗ Make verdicts (that's LLM's job)
  ✗ Understand context (that's LLM's job)
  ✗ Reason about contradictions (that's LLM's job)
```

### The LLM Judge's Role:

```
LLM Judge = Reasoning Engine

What it does:
  ✓ Read claim text
  ✓ Read KB evidence
  ✓ Compare them logically
  ✓ Detect contradictions
  ✓ Detect partial matches
  ✓ Provide reasoning
  
What it DOES NOT do:
  ✗ Store legal knowledge (that's KB's job)
  ✗ Retrieve statutes (that's KB's job)
```

---

## 🎯 Why Both KB AND LLM?

### Problem: Why not just KB?

❌ **KB alone cannot:**
- Understand semantic meaning
- Detect subtle contradictions
- Handle paraphrasing
- Reason about implications

**Example:**
```
Claim: "IT Act penalizes unauthorized access"
KB has: "Section 43... liable to pay damages... for accessing..."

KB match? ✅ Yes (keyword match)
But are they the same? ❌ NO!
  - "penalizes" ≠ "liable to pay damages"
  - Criminal vs civil liability

Need LLM to understand this nuance.
```

### Problem: Why not just LLM?

❌ **LLM alone cannot:**
- Guarantee factual accuracy
- Avoid hallucinations
- Provide legal citations
- Stay updated with law changes

**Example:**
```
Claim: "Section 43A requires compensation"

Without KB:
  LLM might say: "Yes, sounds legal!" (hallucination)
  
With KB:
  LLM checks actual statute text
  LLM says: "Yes, SUPPORTED by evidence" (verified)
```

### Solution: KB + LLM = RAG (Retrieval Augmented Generation)

```
┌───────────┐     ┌───────────┐
│    KB     │────▶│    LLM    │
│ (Facts)   │     │ (Reasoning)│
└───────────┘     └───────────┘
     │                  │
     │                  │
     ▼                  ▼
  Evidence          Verdict
  (Statutes)     (SUPPORTED/
                  CONTRADICTED)
```

**This is called:** **Grounded Generation** or **RAG (Retrieval Augmented Generation)**

---

## 🔄 Complete Request Flow Example

### Input:
```json
POST /api/check
{
  "text": "Section 43A of IT Act provides for imprisonment up to 5 years for data breaches.",
  "context": "Legal advisory"
}
```

### Step-by-Step:

#### 1. Claim Extraction (LLM Call #1)
```
LLM Input: "Section 43A of IT Act provides for imprisonment..."
LLM Output: [
  {
    "text": "Section 43A of IT Act provides for imprisonment up to 5 years for data breaches",
    "type": "SECTION_REF",
    "citation": "Section 43A of IT Act"
  }
]
```

#### 2. KB Lookup (Database + FAISS)
```
PostgreSQL Query:
  SELECT text FROM statute_sections 
  WHERE section_number = '43A' AND act_name = 'IT Act'
  
Result:
  "Section 43A. Compensation for failure to protect data.— 
   Where a body corporate... fails to protect... shall be 
   liable to pay damages by way of compensation..."

FAISS Search:
  Query: "Section 43A imprisonment data breach"
  Top Result: Section 43A (similarity: 0.91)
```

#### 3. LLM Judge (LLM Call #2)
```
LLM Prompt:
  "You are a legal verifier.
   
   Claim: 'Section 43A provides imprisonment up to 5 years'
   
   Evidence: 'Section 43A... liable to pay damages by way 
             of compensation... not exceeding five crore rupees'
   
   Does the evidence support the claim?"

LLM Reasoning:
  "The evidence mentions 'compensation' and 'damages', which 
   indicate civil liability. The claim mentions 'imprisonment', 
   which indicates criminal liability. These are contradictory.
   Section 43A is about compensation, not imprisonment."

LLM Output:
  {
    "verdict": "CONTRADICTED",
    "confidence": 0.97,
    "reasoning": "Section 43A provides civil compensation, not criminal imprisonment"
  }
```

#### 4. Trust Score Calculation
```
Verdicts: [CONTRADICTED]
Trust Index = 0.0 (contradicted = 0.0 weight)
Threshold check: 0.0 < 0.5
Decision: FLAGGED
```

#### 5. Response:
```json
{
  "request_id": "...",
  "decision": "FLAGGED",
  "trust_index": 0.0,
  "claims": [
    {
      "id": "claim_001",
      "text": "Section 43A provides imprisonment...",
      "type": "SECTION_REF"
    }
  ],
  "verdicts": [
    {
      "claim_id": "claim_001",
      "label": "CONTRADICTED",
      "evidence": ["Section 43A... compensation..."],
      "confidence": 0.97,
      "reasoning": "Section 43A provides civil compensation, not criminal imprisonment",
      "stage_reached": 2
    }
  ]
}
```

---

## 🎓 Key Takeaways

1. ✅ **LLM ALWAYS runs** when KB has data (to verify)
2. ✅ **Same model** (`gpt-oss-120b`) for extraction AND judging
3. ✅ **KB provides evidence**, LLM provides reasoning
4. ✅ **Two LLM calls** per request:
   - Call #1: Extract claims
   - Call #2: Judge each claim (can be multiple)
5. ✅ **KB + LLM = RAG** (Retrieval Augmented Generation)
6. ⚠️ **If KB has no data**, LLM cannot judge → UNVERIFIABLE

---

## 📝 Summary Table

| Component | Technology | Role | Model |
|-----------|------------|------|-------|
| **Claim Extraction** | LLM | Decompose text into atomic claims | `openai/gpt-oss-120b` (Groq) |
| **KB Exact Lookup** | PostgreSQL | Find exact section matches | N/A (database) |
| **KB Semantic Search** | FAISS | Find similar sections | `all-MiniLM-L6-v2` (embeddings) |
| **LLM Judge** | LLM | Verify claims against evidence | `openai/gpt-oss-120b` (Groq) |
| **Trust Score** | Algorithm | Aggregate verdicts | N/A (weighted formula) |
| **Decision** | Threshold | SAFE/FLAGGED/ABSTAIN | N/A (if-else logic) |

---

**Last Updated:** September 11, 2026  
**Current Model:** Groq `openai/gpt-oss-120b` for both extraction and judging  
**KB Size:** 115 statutes + 12 case laws = 123 embeddings
