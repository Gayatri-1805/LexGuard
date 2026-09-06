# Person A: Stage 2 — Legal Grounding (Core Differentiator)

## The Critical Question You Asked:
> "LLM would be needed for checking facts, right? How exactly are facts compared from KB? Are you using LLM for checking? Is it a RAG?"

**Short Answer:** NO, it's NOT a traditional RAG. We use **NLI (Natural Language Inference)** to verify facts—a specialized task different from RAG retrieval.

---

## What is NOT Happening (Common Misconception)

### ❌ NOT RAG:
```
RAG = Retrieve documents → Feed to LLM → LLM generates answer
      (LLM is the verifier and answer-generator)

Example (Wrong):
User: "Is Section 43A strict liability?"
RAG: 
  1. Retrieve KB → finds Section 43A text
  2. Passes to LLM: "Based on this KB, answer: Is Section 43A strict liability?"
  3. LLM generates: "Yes, Section 43A imposes strict liability..."
  
Problem: LLM is still the authority; we haven't validated anything
```

### ❌ NOT LLM-as-Verifier:
```
LLM-Verifier = Send claim + evidence to LLM → LLM says "true/false"

Example (Wrong):
Claim: "Section 43A requires proving willful negligence"
Evidence: [Section 43A text from KB]
LLM Prompt: "Is this claim true based on evidence?"
LLM Response: "False, it requires strict liability"

Problem: LLM could hallucinate; we're trusting LLM judgment without proof
```

---

## What IS Happening (Person A's Approach)

### ✅ NLI (Natural Language Inference) Pipeline:

```
STAGE 2: Legal Grounding with NLI

Input: Claim (from Stage 0)
       "Section 43A requires proving willful negligence"

Step 1: Retrieve relevant KB passages
        ├─ Exact lookup: "Section 43A" → found in PostgreSQL
        ├─ Hybrid search: Dense + BM25 → rank top-k passages
        └─ Evidence: "Section 43A: strict liability for failure to protect data"

Step 2: NLI Model (lightweight, task-specific)
        ├─ Input: (Claim, Evidence) pair
        ├─ Model: Fine-tuned DeBERTa-v3-small for NLI
        ├─ Task: 3-way classification (ENTAILED / CONTRADICTED / NEUTRAL)
        └─ Output: Label + confidence score

Step 3: Interpret verdict
        ├─ ENTAILED: Claim is supported by evidence
        │            trust this claim ✓
        │
        ├─ CONTRADICTED: Claim contradicts evidence
        │                 this is a hallucination 🚩
        │
        └─ NEUTRAL: Evidence doesn't prove/disprove claim
                    insufficient grounding, may need Stage 3

Output: Verdict { claim_id, label, evidence, confidence, stage_reached=2 }
```

---

## Key Difference: NLI vs LLM Verification

### NLI (What We Use):

```
Task: Determine logical relationship between two texts

Premise (Evidence): "Section 43A imposes strict liability"
Hypothesis (Claim): "Section 43A requires proving willful negligence"

NLI Model (DeBERTa-v3):
  Input: [premise, hypothesis]
  Output: ENTAILED (0.1) / CONTRADICTED (0.85) / NEUTRAL (0.05)
  
Interpretation:
  - CONTRADICTED (0.85): Premise denies hypothesis ✓ This is proof
  - No LLM judgment, pure linguistic entailment
```

### LLM Verification (What We Avoid):

```
Task: Generate a judgment (prone to hallucination)

Prompt: "Here's evidence: 'Section 43A imposes strict liability'
         Is this claim true: 'Section 43A requires proving willful negligence'?
         Answer: true/false"

LLM Response: Could say "true" even though evidence says the opposite
              (confabulation, context bias, etc.)
```

---

## The Technical Pipeline (Detailed)

### Stage 2a: Retrieval (Get Evidence from KB)

```python
# Step 1: Exact match (fast, deterministic)
def retrieve_exact(claim: str, kb: PostgreSQL):
    """Extract section numbers/case names from claim via regex"""
    section_numbers = re.findall(r'Section\s+(\d+[A-Z]?)', claim)
    
    results = []
    for section_num in section_numbers:
        row = kb.query(f"SELECT text FROM statutes WHERE section_id = %s", section_num)
        if row:
            results.append({
                'section': section_num,
                'text': row.text,
                'source': 'exact_match',
                'score': 1.0  # Perfect match
            })
    return results

# Example:
claim = "Section 43A requires proving willful negligence"
evidence = retrieve_exact(claim, kb)
# Output: [{'section': '43A', 'text': '...strict liability...', 'source': 'exact_match', 'score': 1.0}]
```

### Stage 2b: Dense + Sparse Hybrid Search (if exact match misses)

```python
# Step 2: Dense retrieval (semantic similarity)
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer('bge-small-en-v1.5')
client = QdrantClient(host='localhost', port=6333')

def retrieve_dense(claim: str, kb_vector_store: Qdrant):
    """Embed claim, find similar KB passages"""
    claim_embedding = model.encode(claim)
    
    results = client.search(
        collection_name='legal_kb',
        query_vector=claim_embedding,
        limit=5,
        score_threshold=0.6  # Only high-similarity passages
    )
    
    return [
        {
            'text': result.payload['text'],
            'source': 'dense_retrieval',
            'score': result.score
        }
        for result in results
    ]

# Example:
claim = "Data breach victims must prove negligence"
evidence = retrieve_dense(claim, qdrant)
# Output: [
#   {'text': 'Section 43A: strict liability...', 'source': 'dense_retrieval', 'score': 0.87}
# ]
```

### Stage 2c: NLI Classification (The Verifier)

```python
# Step 3: Use NLI model to compare claim against evidence
from sentence_transformers import CrossEncoder

# Load a lightweight NLI model
nli_model = CrossEncoder('microsoft/deberta-v3-small')
# Or use a legal-specific fine-tuned version if available

def verify_claim_with_nli(claim: str, evidence_passages: list) -> Verdict:
    """
    Use NLI to determine if claim is entailed, contradicted, or neutral w.r.t. evidence
    """
    
    # For each evidence passage, compute entailment
    best_verdict = None
    best_score = 0
    
    for evidence in evidence_passages:
        # NLI input: [premise, hypothesis]
        # premise = evidence (what KB says)
        # hypothesis = claim (what LLM claimed)
        text_pair = [evidence['text'], claim]
        
        # DeBERTa scores the 3-way classification
        scores = nli_model.predict([text_pair])[0]
        # scores = [entailment_score, neutral_score, contradiction_score]
        
        # Determine verdict
        labels = ['ENTAILED', 'NEUTRAL', 'CONTRADICTED']
        max_idx = scores.argmax()
        label = labels[max_idx]
        confidence = scores[max_idx]
        
        # Keep the highest-confidence verdict across all evidence
        if confidence > best_score:
            best_score = confidence
            best_verdict = Verdict(
                claim_id=claim.id,
                label=label,
                evidence=[evidence['text']],
                stage_reached=2,
                confidence=confidence
            )
    
    return best_verdict

# Example:
claim = Claim(id='claim_001', text='Section 43A requires proving willful negligence')
evidence = retrieve_exact(claim.text, kb)
verdict = verify_claim_with_nli(claim.text, evidence)

# NLI Model Computation:
# premise = "Section 43A: Compensation for failure to protect data. Strict liability imposed."
# hypothesis = "Section 43A requires proving willful negligence"
#
# DeBERTa output:
# [entailment: 0.02, neutral: 0.13, contradiction: 0.85]  ← CONTRADICTION!
#
# verdict = Verdict(
#     claim_id='claim_001',
#     label=VerdictLabel.CONTRADICTED,  ← Clear proof of hallucination
#     evidence=['Section 43A: Compensation for failure to protect data...'],
#     confidence=0.85,
#     stage_reached=2
# )
```

---

## Why NLI ≠ LLM Judgment

### Key Advantage: NLI is Task-Specific

```
NLI Models (small, fast, fine-tuned):
├─ Trained on MNLI dataset + legal corpora
├─ Single task: entailment classification
├─ Small models (12M params): DeBERTa-v3-small, RoBERTa-base
├─ Deterministic: Same input → Same output (no hallucination)
├─ Explainable: Attention heads show which tokens matter
└─ Cost: $0 (run locally) or cheap inference API

LLM Judgment (large, expensive, general-purpose):
├─ Trained on broad internet text
├─ Many tasks: generation, reasoning, etc.
├─ Large models (7B-70B+ params)
├─ Stochastic: Can confabulate, show recency bias
├─ Black-box: Hard to debug why it judged something
└─ Cost: $$ per API call (GPT-4, Claude, etc.)
```

---

## Real Example: How Stage 2 Detects Hallucination

### Scenario: User's LLM Claims Something False

**User's LLM output (to check):**
```
"Section 43A of the IT Act requires data breach victims to prove willful 
negligence on the part of the defendant before they can receive compensation."
```

### Stage 0: Decomposition (Person A)
```
Claim extracted:
  - claim_001: "Section 43A requires data protection measures" (SECTION_REF)
  - claim_002: "Data breach victims must prove willful negligence" (PROCEDURAL)
```

### Stage 1: Filter (Person A)
```
Both claims are falsifiable (not generic) → proceed to Stage 2
```

### Stage 2: Grounding (Person A with NLI)

#### For claim_001:
```
Exact lookup: Section 43A found in KB
Evidence: "Section 43A: Compensation for failure to protect data."

NLI Model Input:
  premise: "Section 43A: Compensation for failure to protect data."
  hypothesis: "Section 43A requires data protection measures"
  
NLI Model Output:
  ENTAILED (0.92) ✓  ← Claim is supported by KB

Verdict:
  label = ENTAILED
  confidence = 0.92
  evidence = ["Section 43A: Compensation for failure to protect data..."]
```

#### For claim_002:
```
Dense search: "strict liability" found in KB
Evidence: "Section 43A imposes strict liability. Willfulness or negligence is not required."

NLI Model Input:
  premise: "Section 43A imposes strict liability. Willfulness or negligence is not required."
  hypothesis: "Data breach victims must prove willful negligence"
  
NLI Model Output:
  CONTRADICTED (0.85) 🚩  ← This is a hallucination!

Verdict:
  label = CONTRADICTED
  confidence = 0.85
  evidence = ["Section 43A imposes strict liability..."]
```

### Stage 4: Decision (Person B)
```
entailed_count = 1
contradicted_count = 1
trust_index = 1/2 = 0.5

contradicted_count > 0? YES
contradicted_count >= entailed_count? 1 >= 1? YES
→ decision = FLAGGED 🚩

Final Response:
{
  "decision": "FLAGGED",
  "trust_index": 0.5,
  "claims": [claim_001, claim_002],
  "verdicts": [
    {claim_001: ENTAILED, confidence: 0.92},
    {claim_002: CONTRADICTED, confidence: 0.85}
  ]
}
```

---

## Is This RAG? Why Not?

### RAG Definition:
```
Retrieve docs → Augment LLM prompt → Generate answer
LLM is the decision-maker
```

### This System:
```
Retrieve docs → Compare with NLI → Produce verdict
NLI is the decision-maker (small, specialized model)
LLM is optional (Stage 3 metamorphic testing only)
```

**Key Difference:**
- RAG: LLM generates new content (generation task)
- This: NLI classifies entailment (classification task)

---

## Stage 3: When LLM Gets Involved (Metamorphic Testing)

```
If Stage 2 verdict is NEUTRAL or uncertain, try Stage 3:

Stage 3 Metamorphic Consistency:

1. Rephrase the claim (synonym substitution)
   Original: "Section 43A requires proving willful negligence"
   Rephrase: "To claim compensation, victims must demonstrate defendant negligence"

2. Send both versions to NLI
   original_verdict = NLI(evidence, original) → CONTRADICTED
   rephrase_verdict = NLI(evidence, rephrase) → CONTRADICTED
   
3. If both agree → confidence increases
   If they disagree → escalate to LLM for final call

This is NOT relying on LLM judgment; it's using LLM only for:
- Synonym generation (creative task)
- Final tiebreaker (when NLI is uncertain)
```

---

## KB Storage: PostgreSQL vs Vector DB

```
┌─────────────────────────────────────────┐
│ PostgreSQL: Structured Statute Lookup   │
├─────────────────────────────────────────┤
│ Table: statutes                         │
│ ├─ section_id (indexed): '43A'          │
│ ├─ section_title: 'Compensation...'    │
│ ├─ full_text: '...strict liability...' │
│ └─ source: 'IT_Act_2000'               │
│                                         │
│ Query: Fast exact match                 │
│ SELECT text FROM statutes               │
│ WHERE section_id = '43A'                │
│ Latency: ~1ms (with index)              │
│                                         │
│ Purpose: First pass for section refs    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ Qdrant/FAISS: Dense Vector Search       │
├─────────────────────────────────────────┤
│ Document Embeddings (bge-small)         │
│ ├─ statute_passages[]: 384-dim vectors  │
│ ├─ case_law[]: 384-dim vectors          │
│ └─ regulatory_guidance[]: 384-dim       │
│                                         │
│ Query: Semantic similarity              │
│ Find passages similar to claim          │
│ Latency: ~50-100ms (FAISS local)        │
│          ~500ms (Qdrant over network)   │
│                                         │
│ Purpose: Catch claims that don't exact  │
│          match but reference similar    │
│          legal concepts                 │
└─────────────────────────────────────────┘

Hybrid Approach:
1. Try PostgreSQL exact match first (fast, deterministic)
2. If no match, fall back to Qdrant dense search (semantic)
3. Both return evidence passages
4. Send all evidence to NLI for final verdict
```

---

## Summary: Person A's Stage 2 Architecture

```
                     CLAIM (from Stage 0)
                           │
                    ┌──────┴──────┐
                    │             │
                ┌─EXACT──┐    ┌─SEMANTIC──┐
                │ Lookup │    │  Search   │
                │        │    │           │
           PostgreSQL  Qdrant/FAISS
           (fast)      (thorough)
                │            │
                └────┬───────┘
                     │
              Evidence Passages
                     │
                    ▼
            ┌─────────────────┐
            │  NLI Model      │
            │ (DeBERTa-v3)    │
            │                 │
            │ Entailment      │
            │ Classifier      │
            └─────────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   Verdict       │
            │ ENTAILED /      │
            │ CONTRADICT /    │
            │ NEUTRAL         │
            └─────────────────┘
                     │
                     ▼
            Return to Stage 3/4
```

---

## Key Takeaway

**NOT RAG. NOT LLM Verification.**

**It's NLI Classification:**
- Small, specialized task-specific model
- Compares two texts: claim vs. evidence
- Outputs: ENTAILED / CONTRADICTED / NEUTRAL
- Fast, deterministic, explainable
- Zero hallucination risk (it's a classification, not generation)

When LLM is used (Stage 3), it's only for:
- Generating paraphrases (creative, not judgment)
- Tiebreakers (after NLI gives uncertain results)

This is why it's the **core differentiator** of your system: You replace expensive, hallucination-prone LLM judgment with a lightweight, reliable NLI pipeline grounded in law.
