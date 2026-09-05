# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-05

### Added

**Knowledge Base Layer (Person B)**
- PostgreSQL backend with 115 IT Act statute sections and 12 case law entries
- Exact-match lookup via `lookup_section(section_ref, act_name)`
- Semantic search fallback via FAISS vector index (all-MiniLM-L6-v2, 384 dims, 123 embeddings)
- Vector retrieval with confidence scoring
- Analytics database with `check_logs` table for persistence
- KB interface abstraction (`kb_interface.py`) for Stage 2 integration

**API Service (Person B)**
- FastAPI application with CORS middleware
- `POST /api/check` endpoint accepting CheckRequest, returning CheckResponse
- Background analytics logging (non-blocking)
- `GET /api/analytics/summary` for aggregate stats (30-day default)
- `GET /api/analytics/checks` paginated list of recent checks
- `GET /api/analytics/flagged` for flagged claims (decision != SAFE)
- `GET /health` for uptime monitoring
- Swagger UI at `/docs` and ReDoc at `/redoc`

**Pipeline Stub (Person A)**
- Realistic CheckResponse generator for testing
- Supports SECTION_REF, CASE_CITATION, HOLDING, PROCEDURAL claim types
- Generates ENTAILED, CONTRADICTED, NOT_ENOUGH_INFO verdicts
- Computes trust_index (0-1) and decides SAFE/FLAGGED/ABSTAIN
- One-line swap to real pipeline when Person A completes it

**Python SDK (Person B)**
- `HallucinationDetectorClient` class using httpx
- Methods: `check()`, `get_summary()`, `get_checks()`, `get_flagged()`
- Custom `DetectorAPIError` exception
- Type hints and docstrings
- Installable via `pip install legal-hallucination-sdk`

**TypeScript/npm SDK (Person B)**
- `HallucinationDetectorClient` class using native fetch
- Auto-generated types from OpenAPI schema
- Methods: `check()`, `getSummary()`, `getChecks()`, `getFlagged()`
- React and Vue integration examples
- Publishable to npm

**Documentation**
- `README.md` with project overview and quick start
- `ARCHITECTURE.md` with system design and data flow
- `GETTING_STARTED.md` with step-by-step setup guide
- `API.md` with endpoint reference and examples
- `SDK_USAGE.md` with client library examples
- `DEPLOYMENT.md` with production deployment guides
- `CONTRIBUTING.md` with development guidelines
- `CHANGELOG.md` (this file)

**DevOps**
- `docker-compose.yml` with PostgreSQL, API, Redis (optional), Qdrant (optional)
- `Dockerfile` for containerized API deployment
- `.env.example` with all configuration variables
- `.gitignore` with Python, Node.js, and secrets exclusions
- `openapi-sync.sh` for OpenAPI schema generation and TypeScript type generation

**Testing**
- `test_api.py` comprehensive API test suite (5 tests)
- `test_retrieval.py` vector KB retrieval sanity check
- `test_full_kb.py` full KB flow (exact lookup + semantic + case law)
- Python SDK tests (unit and integration examples in `SDK_USAGE.md`)

### Known Limitations

- API has no authentication (adds auth in production deployment)
- CORS allows all origins (restrict before production)
- Vector index rebuilt from DB on each startup (cache in memory for scale)
- Qdrant support not yet implemented (using FAISS for MVP)
- Redis caching not yet integrated
- No rate limiting (implement before production)
- Fabricated test cases in KB are only for evaluation (filtered from retrieval)

### Testing

- ✅ Swagger UI: `/docs` interactive endpoint testing
- ✅ Health endpoint: Returns 200 OK
- ✅ POST /check: Returns CheckResponse with correct schema
- ✅ Analytics endpoints: Query and return data correctly
- ✅ Python SDK: Client class works with real API
- ✅ TypeScript SDK: Types generated, compiles successfully
- ✅ Background logging: Check records persist to analytics DB

### Contributors

- Person A: Detection Pipeline (stub)
- Person B: API, Knowledge Base, SDKs
- Person C: (Dashboard in progress)

---

## [Unreleased]

### Planned

**Person A: Detection Pipeline**
- Stage 0: Decompose → extract atomic claims from unstructured text
- Stage 1: Filter → remove non-falsifiable claims
- Stage 2: Ground → verify against KB using lookup + semantic search
- Stage 3: Metamorphic → consistency testing (if A → B and B → C, then A → C)
- Stage 4: Trust Score → weighted aggregation of verdicts

**Person B: Enhancements**
- API authentication (OAuth2, API keys)
- Rate limiting (100 req/min default)
- Caching layer (Redis for KB queries)
- Request validation and sanitization
- Comprehensive error handling and logging

**Person C: Dashboard & Evaluation**
- React/Vue frontend for analytics visualization
- Gold set evaluation data (100+ manually-scored texts)
- Scoring metrics (precision, recall, F1 by claim type)
- Corruption generator for hallucination injection testing
- Dashboard views:
  - Aggregate stats (chart over time)
  - Recent checks (paginated table)
  - Flagged claims (for manual review)

### Breaking Changes

None yet (v0.1.0 is MVP).

---

## Commit History

See `git log` for full commit history.

Key milestones:
- Initial scaffold with shared schemas
- Knowledge base ingestion (115 statutes + 12 cases)
- Vector index building (FAISS)
- FastAPI routes (check, analytics)
- Analytics models and persistence
- Python and TypeScript SDKs
- OpenAPI schema generation
- Comprehensive documentation

