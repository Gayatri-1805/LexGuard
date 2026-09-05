# System Architecture

## Overview

The Legal Hallucination Detector is a 3-person capstone project built as a **modular, multi-stage pipeline** for detecting false claims in legal domain LLM outputs.

Architecture follows a **three-layer decomposition**:

```
┌─────────────────────────────────────────────────────────┐
│  Client SDKs (Python, TypeScript)                       │
│  + HTTP REST API (FastAPI)                              │
├─────────────────────────────────────────────────────────┤
│  Person B: API & Knowledge Base Layer                   │
│  + PostgreSQL (structured KB: statutes, case law)       │
│  + FAISS (semantic search via embeddings)               │
├─────────────────────────────────────────────────────────┤
│  Person A: Detection Pipeline (Stages 0-4)             │
│  + Stage 0: Decompose → extract atomic claims           │
│  + Stage 1: Filter → remove non-falsifiable claims      │
│  + Stage 2: Ground → verify against KB                  │
│  + Stage 3: Metamorphic → consistency testing           │
│  + Stage 4: Trust Score → aggregate & decide            │
├─────────────────────────────────────────────────────────┤
│  Person C: Analytics & Dashboard                        │
│  + PostgreSQL analytics_db (check logs, metrics)        │
│  + React/Vue Dashboard (visualization)                  │
│  + Evaluation module (gold set, scoring)                │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Claim Detection Flow

```
1. Client sends: CheckRequest
   {
     "text": "Section 43A requires compensation for data breach.",
     "context": "Legal analysis"
   }

2. API Router (/check) receives request
   ↓
3. Person A Pipeline processes:
   Stage 0 → Extract claims: ["Section 43A requires compensation..."]
   Stage 1 → Filter: [keep if falsifiable]
   Stage 2 → Ground against KB:
      - lookup_section("43A", "IT Act") → get statute text
      - retrieve("data breach compensation") → semantic search
   Stage 3 → Metamorphic: test consistency with related claims
   Stage 4 → Trust Score: aggregate evidence → compute score (0-1)
   ↓
4. Pipeline returns: CheckResponse
   {
     "claims": [...],
     "verdicts": [...],
     "trust_index": 0.92,
     "decision": "SAFE"  // or FLAGGED / ABSTAIN
   }

5. Background task logs to analytics DB (non-blocking)
   ↓
6. API returns response to client immediately
   ↓
7. Client SDK receives CheckResponse
```

---

## Component Details

### Person A: Detection Pipeline

**File:** `detection-engine/pipeline.py`

**Stages:**

| Stage | Input | Output | Purpose |
|-------|-------|--------|---------|
| **0 (Decompose)** | Raw LLM text | Atomic claims | Break down into testable sub-claims |
| **1 (Filter)** | Claims | Filtered claims | Remove non-falsifiable (opinions, procedural) |
| **2 (Ground)** | Filtered claims | Verdicts + evidence | Verify against KB via exact lookup or semantic search |
| **3 (Metamorphic)** | Verdicts | Refined verdicts | Test consistency (if A → B and B → C, then A → C?) |
| **4 (Trust Score)** | All verdicts | trust_index + decision | Aggregate with weights, threshold to SAFE/FLAGGED/ABSTAIN |

**Dependencies:**
- `shared/schemas.py` — Claim, Verdict, CheckResponse models
- `api/kb/kb_interface.py` — Abstract KB interface (lookup_section, retrieve)
- `shared/config.py` — Weights, thresholds, LLM model name

**Key Classes:**
- `Claim` — atomic legal claim with type (CASE_CITATION, SECTION_REF, HOLDING, PROCEDURAL)
- `Verdict` — verdict for a claim (ENTAILED, CONTRADICTED, NOT_ENOUGH_INFO, LOW_RISK_SKIP)
- `CheckResponse` — final output with all claims, verdicts, trust_index, decision

---

### Person B: API & Knowledge Base

**API File:** `api-and-sdk/api/main.py`

**Routes:**

```
POST /api/check
  Input:  CheckRequest (text, context, request_id)
  Output: CheckResponse (claims, verdicts, trust_index, decision)
  Side Effect: Background task logs to check_logs table

GET /api/analytics/summary?days=30
  Output: {total_checks, safe/flagged/abstain counts, avg_trust_index}

GET /api/analytics/checks?limit=50&offset=0
  Output: {total, checks: [{request_id, trust_index, decision, created_at}]}

GET /api/analytics/flagged?limit=50&offset=0
  Output: {total, flagged_checks: [same as above]}

GET /health
  Output: {status: "ok"}
```

**Knowledge Base Layer:**

```
api/kb/
├── kb_interface.py       # Abstract base (Person A depends on this)
│   ├── lookup_section(section_ref, act_name) → str | None
│   └── retrieve(query, top_k) → list[str]
│
├── postgres_kb.py        # Exact-match implementation
│   └── Queries statute_sections & case_law tables
│
├── vector_kb.py          # Semantic search via FAISS
│   └── VectorRetriever class (loads faiss index + metadata)
│
├── embeddings.py         # Embedding service
│   └── all-MiniLM-L6-v2 (384 dims, normalized)
│
├── models.py             # SQLAlchemy ORM
│   ├── StatuteSection (115 rows, IT Act)
│   └── CaseLaw (12 rows, verified + test cases)
│
├── db.py                 # SessionLocal, get_db() dependency
│
├── build_index.py        # Build FAISS index from DB
│
└── index/                # (gitignored, rebuildable)
    ├── it_act.faiss      # FAISS index
    └── it_act_metadata.json
```

**Statistics:**
- 115 IT Act statute sections indexed
- 12 case law entries (8 verified real cases, 4 fabricated test cases)
- 123 total embeddings in FAISS index
- All indexed rows have `is_verified=true` (fabricated cases excluded from retrieval)

---

### Person B: SDKs

**Python SDK:** `sdk-python/legal_hallucination_sdk/client.py`

```python
client = HallucinationDetectorClient(base_url="http://localhost:8000/api")

# Check for hallucinations
response = client.check(text="Section 43A...", context="Legal analysis")
print(response["decision"])      # SAFE, FLAGGED, or ABSTAIN
print(response["trust_index"])   # 0-1

# Get analytics
summary = client.get_summary(days=30)
flagged = client.get_flagged(limit=10)
```

**TypeScript SDK:** `sdk-npm/src/client.ts`

```typescript
const client = new HallucinationDetectorClient('http://localhost:8000/api');

const response = await client.check({
  text: 'Section 43A...',
  context: 'Legal analysis'
});

console.log(response.decision);  // SAFE, FLAGGED, or ABSTAIN
```

Types auto-generated from OpenAPI schema (run `bash openapi-sync.sh`).

---

### Person C: Analytics & Dashboard

**Analytics DB:** `analytics-db/models.py`

```
check_logs table:
  id              (PK)
  request_id      (FK to CheckResponse.request_id, indexed)
  trust_index     (0-1 float)
  decision        (SAFE, FLAGGED, ABSTAIN)
  created_at      (UTC timestamp, indexed for time-range queries)
```

**Dashboard Endpoints Consumed:**
- `/analytics/summary` — line chart of trust_index over time
- `/analytics/checks` — paginated table of recent checks
- `/analytics/flagged` — priority list for manual review

**Evaluation Module:** `eval/`
- Gold set: 100+ manually-scored legal texts
- Corruption generator: inject hallucinations for testing
- Scoring: precision, recall, F1 by claim type

---

## Integration Points

### Person A ↔ Person B

**Contract:** `shared/schemas.py`

- Person A produces: `CheckResponse`
- Person B consumes: `CheckResponse` (returns to client via API)
- Person A calls: `kb_interface.retrieve()` during Stage 2

**How it works:**
```
Person A:
  response = check(text="Section 43A...", context="...")
  # internally calls kb.lookup_section() and kb.retrieve()

Person B:
  @app.post("/api/check")
  async def check_hallucination(request: CheckRequest, background_tasks):
    response = PIPELINE_CHECK_FN(request.text, request.context)
    background_tasks.add_task(log_check_to_db, ...)
    return response
```

### Person B ↔ Person C

**Contract:** Analytics endpoints

- Person B exposes: `/analytics/*` routes
- Person C queries: these endpoints for dashboard data
- Person B logs: every check to `check_logs` table

---

## Deployment Architecture

### Local Development

```
┌─ Docker Compose
│  ├─ PostgreSQL (Neon via connection string, or local)
│  ├─ Redis (optional, for caching)
│  └─ Qdrant (optional, for vector DB alternative)
├─ Python venv
│  └─ uvicorn api.main:app --reload
├─ Node.js
│  └─ npm run dev (dashboard)
└─ Browser
   └─ http://localhost:8000/docs (Swagger API)
```

### Production

```
┌─ Cloud Platform (AWS/GCP/Azure)
│  ├─ Managed PostgreSQL (Neon)
│  ├─ Container Registry (ECR/GAR/ACR)
│  ├─ Orchestration (ECS/Cloud Run/AKS)
│  └─ CDN (CloudFront/Cloud CDN)
├─ API Container
│  └─ uvicorn with gunicorn
├─ Dashboard Container
│  └─ nginx serving static React/Vue
└─ Load Balancer
   └─ HTTPS, rate limiting, auth
```

---

## Security Considerations

**In Development:**
- CORS allows all origins (localhost only, see main.py)
- No authentication on endpoints
- .env file with real DATABASE_URL (gitignored, never committed)

**Before Production:**
- Restrict CORS origins
- Add API key / OAuth2 authentication
- Use HTTPS/TLS
- Add rate limiting (e.g., 100 req/min per IP)
- Implement audit logging for all checks
- Use secrets manager for API keys (AWS Secrets Manager, etc.)
- Sanitize inputs to prevent injection attacks
- Add request validation and sanitization

---

## Performance Considerations

**Latency Targets:**
- `/check` endpoint: <500ms (p95)
  - Pipeline: ~300ms
  - KB retrieval: ~50ms
  - DB logging: background (non-blocking)
  - Total: ~350ms

**Throughput:**
- FastAPI async: supports 100+ concurrent requests
- PostgreSQL: 1000+ queries/sec on moderate hardware
- FAISS search: 50ms for 123 vectors (negligible as scale increases)

**Caching Opportunities:**
- KB queries could cache statute text (rarely changes)
- OpenAI responses could cache common phrases
- Analytics queries cache with 1-hour TTL

---

## Testing Strategy

**Unit Tests:**
- Stages 0-4 logic (Person A)
- KB retrieval correctness (Person B)
- SDK client error handling (Person B)

**Integration Tests:**
- Full pipeline end-to-end
- API routes (health, check, analytics)
- DB persistence and retrieval

**Evaluation:**
- Gold set scoring (Person C)
- Precision/recall by claim type
- Confidence calibration

**Load Testing:**
- 100 concurrent /check requests
- 1000 analytics queries per minute

---

## Maintenance & Scaling

**As volume grows:**
1. Add read replicas to PostgreSQL for analytics queries
2. Cache FAISS index in memory with LRU eviction
3. Archive old check_logs to cold storage (>90 days)
4. Add Elasticsearch for full-text search of claims
5. Implement async job queue (Celery) for heavy pipeline work

**Monitoring:**
- Track pipeline latency by stage
- Monitor API error rates and 500s
- Alert on trust_index distribution shifts
- Dashboard uptime and responsiveness

---

## File Organization

```
legal-hallucination-detector/
├── shared/                          # All 3 people import
│   ├── schemas.py                   # Pydantic models
│   ├── config.py                    # Config + env vars
│   └── __init__.py
│
├── detection-engine/                # Person A
│   ├── pipeline.py                  # Main entry point
│   ├── stages/
│   │   ├── stage0_decompose.py
│   │   ├── stage1_filter.py
│   │   ├── stage2_ground.py
│   │   ├── stage3_metamorphic.py
│   │   └── stage4_trust_score.py
│   ├── judge_client.py              # LLM interaction
│   └── __init__.py
│
├── api-and-sdk/                     # Person B
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   ├── routes/
│   │   │   ├── check.py             # POST /check
│   │   │   └── analytics.py         # GET /analytics/*
│   │   ├── analytics/
│   │   │   ├── models.py            # CheckLog ORM
│   │   │   └── init_db.py
│   │   ├── kb/                      # Knowledge Base
│   │   │   ├── kb_interface.py
│   │   │   ├── postgres_kb.py
│   │   │   ├── vector_kb.py
│   │   │   ├── embeddings.py
│   │   │   ├── models.py
│   │   │   ├── db.py
│   │   │   ├── build_index.py
│   │   │   └── index/               # (gitignored)
│   │   └── pipeline_stub.py
│   ├── sdk-python/
│   │   ├── legal_hallucination_sdk/
│   │   │   ├── client.py
│   │   │   └── __init__.py
│   │   └── pyproject.toml
│   ├── sdk-npm/
│   │   ├── src/
│   │   │   ├── client.ts
│   │   │   └── generated-types.ts   # (auto-generated)
│   │   ├── package.json
│   │   └── tsconfig.json
│   ├── requirements.txt
│   ├── openapi-sync.sh
│   ├── run_api.py
│   ├── test_api.py
│   └── .env.example
│
├── dashboard-and-eval/              # Person C
│   ├── dashboard/                   # React/Vue frontend
│   ├── analytics-db/
│   │   ├── models.py
│   │   └── migrations/
│   ├── eval/
│   │   ├── gold_set/
│   │   ├── scoring.py
│   │   └── corruption_generator.py
│   └── requirements.txt
│
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── ARCHITECTURE.md                  # This file
├── GETTING_STARTED.md
├── API.md
├── SDK_USAGE.md
├── DEPLOYMENT.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── LICENSE
```

---

## References

- **Pydantic v2**: https://docs.pydantic.dev/latest/
- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **FAISS**: https://github.com/facebookresearch/faiss
- **sentence-transformers**: https://www.sbert.net/
