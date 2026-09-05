# Legal Hallucination Detector

[![CI](https://github.com/yourusername/legal-hallucination-detector/workflows/CI/badge.svg)](https://github.com/yourusername/legal-hallucination-detector/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> A 3-person capstone project to detect and score LLM hallucinations in legal domain using multi-stage verification, packaged as HTTP API with Python/TypeScript SDKs and analytics dashboard.

---

## 🎯 Project Overview

This project builds an **LLM hallucination detection pipeline for legal domain** that:

1. **Decomposes** unstructured LLM output into atomic legal claims
2. **Filters** non-falsifiable statements (opinions, procedural)
3. **Grounds** claims against legal knowledge bases (statutes, case law)
4. **Tests** via metamorphic relations for logical consistency
5. **Scores** credibility using weighted evidence aggregation

The result is a **trust_index** (0-1) and **decision** (SAFE / FLAGGED / ABSTAIN) for each text.

**Example:**
```
Input:  "Section 43A requires proving willful negligence for data breach compensation."
Result: FLAGGED (trust_index: 0.18)
        Claim contradicted by evidence:
        "Section 43A imposes strict liability. Willfulness not required."
```

---

## 📦 What's Included

### Person A: Detection Pipeline (Stages 0-4)
- Claim decomposition and classification
- Falsifiability filtering
- Knowledge base grounding
- Metamorphic consistency testing
- Trust score aggregation

**Status:** 🔲 Stub ready for integration

### Person B: API & SDKs ✅
- **API:** FastAPI service with `/check`, `/analytics/*` endpoints
- **KB:** 115 IT Act statute sections + 12 case law entries (FAISS indexed)
- **SDKs:** Python and TypeScript clients
- **Status:** ✅ **Complete & Tested**

### Person C: Dashboard & Evaluation (In Progress)
- React/Vue analytics dashboard
- Gold set evaluation framework
- Hallucination corruption generator
- Scoring metrics

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ & Node.js 16+
- PostgreSQL (Neon free tier recommended)
- Docker & Docker Compose (optional)

### 1-Minute Setup

```bash
# Clone
git clone https://github.com/yourusername/legal-hallucination-detector.git
cd legal-hallucination-detector

# Install
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e api-and-sdk/

# Configure
cp .env.example .env
# Edit .env: add DATABASE_URL, JUDGE_MODEL, API keys

# Initialize
cd api-and-sdk
python -m api.analytics.init_db
python -m api.kb.build_index

# Run
python run_api.py
```

**Open browser:** http://localhost:8000/docs → try `/api/check` endpoint

**Full guide:** See [GETTING_STARTED.md](GETTING_STARTED.md)

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design, data flow, component details |
| [GETTING_STARTED.md](GETTING_STARTED.md) | Step-by-step setup guide with troubleshooting |
| [API.md](API.md) | Endpoint reference with curl/Python/TypeScript examples |
| [SDK_USAGE.md](SDK_USAGE.md) | Client library usage (Python & TypeScript) |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment (Docker, AWS, GCP, Heroku) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow and coding standards |

---

## 📁 Project Structure

```
legal-hallucination-detector/
├── shared/                          # Shared schemas & config (all 3 people import)
│   ├── schemas.py                   # Pydantic models (Claim, Verdict, CheckResponse)
│   └── config.py                    # Configuration management
│
├── detection-engine/                # Person A: Pipeline stages 0-4
│   ├── pipeline.py                  # Main entry point
│   ├── stages/                      # Stage 0-4 implementations
│   └── judge_client.py              # LLM integration
│
├── api-and-sdk/                     # Person B: API & SDKs ✅
│   ├── api/
│   │   ├── main.py                  # FastAPI app
│   │   ├── routes/                  # /check, /analytics endpoints
│   │   ├── analytics/               # CheckLog models
│   │   └── kb/                      # Knowledge Base (postgres, vector, embeddings)
│   ├── sdk-python/                  # Python SDK (installable)
│   ├── sdk-npm/                     # TypeScript SDK (npm package)
│   ├── requirements.txt
│   ├── run_api.py                   # Start API server
│   └── test_api.py                  # API test suite
│
├── dashboard-and-eval/              # Person C: Dashboard & Eval (In progress)
│   ├── dashboard/                   # React/Vue frontend
│   ├── analytics-db/                # Analytics models
│   └── eval/                        # Gold set, scoring
│
├── docker-compose.yml               # PostgreSQL + API + Redis + Qdrant
├── Dockerfile
├── .env.example                     # Configuration template
├── .gitignore
├── LICENSE                          # MIT
├── README.md                        # This file
├── ARCHITECTURE.md
├── GETTING_STARTED.md
├── API.md
├── SDK_USAGE.md
├── DEPLOYMENT.md
├── CONTRIBUTING.md
└── CHANGELOG.md
```

---

## 🏗️ Architecture Overview

```
                            Client (Python/TypeScript SDK)
                                      ↓
                    FastAPI REST API (Port 8000)
                    ├─ POST /api/check
                    ├─ GET /api/analytics/summary
                    ├─ GET /api/analytics/checks
                    └─ GET /api/analytics/flagged
                                      ↓
                    ┌─────────────────────────────────┐
                    │  Person A: Pipeline (Stages 0-4) │
                    │  - Decompose claims              │
                    │  - Filter non-falsifiable        │
                    │  - Ground against KB (Stage 2)   │
                    │  - Test consistency              │
                    │  - Compute trust score           │
                    └─────────────────────────────────┘
                                      ↓
                    ┌─────────────────────────────────┐
                    │  Person B: Knowledge Base         │
                    ├─ PostgreSQL (Statutes + Cases)   │
                    └─ FAISS Index (Semantic Search)   │
                                      ↓
                    ┌─────────────────────────────────┐
                    │  Person C: Analytics             │
                    ├─ PostgreSQL (check_logs table)   │
                    └─ Dashboard (visualization)       │
                    └─ Eval (gold set, scoring)        │
```

---

## 📊 Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Knowledge Base** | ✅ Complete | 115 statutes + 12 cases indexed |
| **API Service** | ✅ Complete | All endpoints working, tested |
| **Analytics DB** | ✅ Complete | Logging and querying functional |
| **Python SDK** | ✅ Complete | Ready to pip install |
| **TypeScript SDK** | ✅ Complete | Types auto-generated, ready to npm publish |
| **Pipeline (Stages 0-4)** | 🔲 Stub | Ready for Person A integration |
| **Dashboard** | ⏳ In Progress | Person C building frontend |
| **Evaluation** | ⏳ In Progress | Gold set and metrics in progress |

---

## 🔌 API Examples

### Check for Hallucinations

```bash
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Section 43A requires strict liability for data protection failures.",
    "context": "Legal analysis document"
  }'
```

**Response:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "claims": [{"id": "claim_001", "text": "Section 43A requires strict liability...", "type": "SECTION_REF"}],
  "verdicts": [{"claim_id": "claim_001", "label": "ENTAILED", "evidence": ["Section 43A: Compensation for failure..."], "confidence": 0.92}],
  "trust_index": 0.92,
  "decision": "SAFE",
  "created_at": "2026-09-05T11:28:28.631281Z"
}
```

### Get Analytics Summary

```bash
curl http://localhost:8000/api/analytics/summary?days=30
```

**Response:**
```json
{
  "total_checks": 1234,
  "checks_safe": 1000,
  "checks_flagged": 200,
  "checks_abstain": 34,
  "avg_trust_index": 0.81,
  "date_range": {"from": "2026-08-05", "to": "2026-09-05"}
}
```

**See [API.md](API.md) for full endpoint documentation.**

---

## 🐍 Python SDK

```python
from legal_hallucination_sdk import HallucinationDetectorClient

client = HallucinationDetectorClient('http://localhost:8000/api')

# Check text
response = client.check(text='Section 43A...', context='Legal analysis')
print(response['decision'])  # SAFE, FLAGGED, or ABSTAIN

# Get analytics
summary = client.get_summary(days=30)
flagged = client.get_flagged(limit=50)
```

**See [SDK_USAGE.md](SDK_USAGE.md) for full examples (batch processing, error handling, etc.).**

---

## 📘 TypeScript SDK

```typescript
import { HallucinationDetectorClient } from '@legal-hallucination/sdk';

const client = new HallucinationDetectorClient('http://localhost:8000/api');

const response = await client.check({
  text: 'Section 43A...',
  context: 'Legal analysis'
});

console.log(response.decision);  // SAFE, FLAGGED, or ABSTAIN
```

---

## 🚢 Deployment

### Docker (Recommended)

```bash
docker-compose up -d
```

Starts PostgreSQL + API + optional Redis/Qdrant.

### Cloud Platforms

- **AWS ECS** — See [DEPLOYMENT.md](DEPLOYMENT.md#aws-ecs)
- **Google Cloud Run** — See [DEPLOYMENT.md](DEPLOYMENT.md#google-cloud-run)
- **Heroku** — See [DEPLOYMENT.md](DEPLOYMENT.md#heroku)

---

## 🧪 Testing

```bash
# Run API tests
python test_api.py

# Run unit tests (when available)
pytest tests/ -v

# Check TypeScript
cd sdk-npm && npm run build
```

---

## 🤝 Contributing

We welcome contributions from all 3 people and collaborators!

1. **Read [CONTRIBUTING.md](CONTRIBUTING.md)** for workflow and coding standards
2. **Create a branch:** `git checkout -b feature/your-feature`
3. **Make changes, test locally**
4. **Format code:** `black . && flake8 .`
5. **Push & open PR**
6. **Wait for CI ✅ and review**

### Development Setup

```bash
git clone ...
cd legal-hallucination-detector
python -m venv venv && source venv/bin/activate
pip install -e api-and-sdk/ -e api-and-sdk/sdk-python/
pip install pytest black flake8 mypy
```

---

## 📋 Roadmap

**Version 0.2.0 (Q4 2026)**
- Person A: Complete pipeline stages 0-4
- Person B: Add API authentication & rate limiting
- Person C: Dashboard MVP

**Version 1.0.0 (Q1 2027)**
- Evaluate against gold set
- Performance optimization
- Production deployment
- Public SDK release (PyPI, npm)

---

## 📝 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- **Neon** for free PostgreSQL hosting
- **Hugging Face** for embedding models and dataset hosting
- **FAISS** by Meta for vector search
- **FastAPI** for amazing web framework

---

## 💬 Support

- **Questions?** Open a [GitHub Discussion](https://github.com/yourusername/legal-hallucination-detector/discussions)
- **Found a bug?** Create a [GitHub Issue](https://github.com/yourusername/legal-hallucination-detector/issues)
- **Need help?** Check [GETTING_STARTED.md](GETTING_STARTED.md#troubleshooting)

---

**Made with ❤️ by the HALO Team**


