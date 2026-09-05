# Getting Started

## Prerequisites

- **Python 3.10+** — Download from https://www.python.org/
- **Node.js 16+** — Download from https://nodejs.org/
- **Docker & Docker Compose** (optional) — https://www.docker.com/
- **Git** — https://git-scm.com/
- **API Keys** (for LLM judge):
  - OpenAI or Anthropic API key
  - Neon PostgreSQL connection string (free tier: https://console.neon.tech)

---

## 1. Clone & Setup

```bash
# Clone repository
git clone https://github.com/yourusername/legal-hallucination-detector.git
cd legal-hallucination-detector

# Create Python virtual environment
python -m venv venv

# Activate venv
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Verify Python version
python --version  # Should be 3.10+
```

---

## 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
# Required:
#   DATABASE_URL=postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require
#   JUDGE_MODEL=claude-3-opus
#   OPENAI_API_KEY=sk-...

# On Windows, you can use:
# (Use any text editor: VS Code, Notepad++, etc.)
# Just make sure DATABASE_URL and JUDGE_MODEL are filled in
```

---

## 3. Install Dependencies

```bash
# Install Python dependencies for api-and-sdk
cd api-and-sdk
pip install -q -r requirements.txt

# This installs:
# - FastAPI, uvicorn (API)
# - SQLAlchemy, psycopg2 (Database)
# - sentence-transformers, faiss-cpu (Embeddings)
# - httpx (SDK client)
# - python-dotenv (Config)
```

---

## 4. Initialize Knowledge Base

```bash
# From api-and-sdk directory
python -m api.analytics.init_db

# This creates the check_logs table in PostgreSQL
# Expected output: ✓ Database initialized
```

---

## 5. Build Vector Index

```bash
# From api-and-sdk directory
python -m api.kb.build_index

# This:
# 1. Fetches 115 statute sections + 8 verified cases from DB
# 2. Embeds all text using all-MiniLM-L6-v2 model (~15 MB download)
# 3. Creates FAISS index in api/kb/index/
# Expected output: Indexed chunks: 115 statute + 8 case = 123 total
```

---

## 6. Start API Server

```bash
# From api-and-sdk directory
python run_api.py

# Or use uvicorn directly:
# python -m uvicorn api.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

**Keep this terminal open.** The API is now running on `http://127.0.0.1:8000`

---

## 7. Test API in Browser

Open your browser and go to:

```
http://127.0.0.1:8000/docs
```

You'll see **Swagger UI** with all endpoints. Try this:

1. Click **"Check Hallucination"** (POST /api/check)
2. Click **"Try it out"**
3. Enter this in the request body:
   ```json
   {
     "text": "Section 43A requires data protection measures.",
     "context": "Legal analysis"
   }
   ```
4. Click **"Execute"**
5. You should see a CheckResponse with `decision: SAFE`

---

## 8. Verify Analytics

In the same Swagger UI, try these endpoints:

```
GET /api/analytics/summary?days=30
  → Shows total checks, avg trust_index

GET /api/analytics/checks?limit=50&offset=0
  → Shows your test check recorded

GET /health
  → Should return {status: "ok"}
```

---

## 9. Test Python SDK

```bash
# In a new terminal (API still running)
python -c "
from legal_hallucination_sdk import HallucinationDetectorClient

client = HallucinationDetectorClient('http://localhost:8000/api')
response = client.check(text='Section 43A requires data protection.', context='Legal')
print(f'Decision: {response[\"decision\"]}')
print(f'Trust: {response[\"trust_index\"]}')
"
```

---

## 10. Generate OpenAPI Schema & TypeScript Types

```bash
# From api-and-sdk directory
bash openapi-sync.sh

# On Windows without bash, use:
# python -c "import json; from api.main import app; schema = app.openapi(); f = open('openapi.json', 'w'); json.dump(schema, f, indent=2); f.close(); print('✓ openapi.json created')"
# npx openapi-typescript openapi.json -o sdk-npm/src/generated-types.ts

# Expected output:
# ✓ Schema saved to openapi.json
# ✓ TypeScript types generated: sdk-npm/src/generated-types.ts
```

---

## 11. Build TypeScript SDK (Optional)

```bash
cd sdk-npm
npm install
npm run build

# Expected output:
# dist/client.js
# dist/client.d.ts
```

---

## 12. Run Comprehensive Tests

```bash
# From api-and-sdk directory (API still running)
python test_api.py

# This runs 5 tests:
# 1. GET /health
# 2. POST /check with sample text
# 3. GET /analytics/summary
# 4. GET /analytics/checks
# 5. GET /analytics/flagged

# Expected: All tests pass ✓
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'shared'"

**Fix:** Ensure you're running from the project root (`legal-hallucination-detector/`) or use `python run_api.py` which sets PYTHONPATH correctly.

### "psycopg2 installation failed" (Windows)

**Fix:** Use `psycopg2-binary` instead:
```bash
pip install psycopg2-binary
```

### "SSL: CERTIFICATE_VERIFY_FAILED" when downloading embeddings

**Fix:** This is fixed by `pip install pip-system-certs`. If still failing:
```bash
pip install --upgrade certifi
```

### API returns 500 on `/check`

**Fix:** Check the API terminal for error messages. Common issues:
- `pipeline_stub.py` not importable (check PYTHONPATH)
- Database connection error (check DATABASE_URL in .env)
- Embeddings model not cached (run `python -m api.kb.build_index` again)

### "Port 8000 already in use"

**Fix:** Use a different port:
```bash
python run_api.py --port 8001
```

Or kill the existing process:
```bash
# On macOS/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Next Steps

1. **For Person A (Detection Engine):**
   - Start implementing `detection-engine/pipeline.py`
   - Use `shared/schemas.py` for data contracts
   - Call `kb_interface.retrieve()` in Stage 2

2. **For Person B (API & SDKs):**
   - Already done! API is running
   - SDKs are ready to publish
   - Next: integrate Person A's real pipeline

3. **For Person C (Dashboard & Eval):**
   - Start building dashboard that queries `/analytics/*` endpoints
   - Create gold set evaluation data in `eval/gold_set/`
   - Implement scoring in `eval/scoring.py`

---

## Running Each Service Separately

### Person A: Detection Pipeline

```bash
# From project root
python -m detection_engine.pipeline
```

### Person B: API Server

```bash
# From api-and-sdk directory
python run_api.py
```

Swagger UI: http://127.0.0.1:8000/docs

### Person C: Dashboard (when built)

```bash
cd dashboard-and-eval/dashboard
npm install
npm run dev
```

---

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# Install new package
pip install package_name

# Freeze dependencies
pip freeze > requirements.txt

# Run tests
pytest tests/

# Format code
black .

# Type check
mypy .

# Lint
flake8 .

# Start API
python run_api.py

# Build vector index
python -m api.kb.build_index

# Generate OpenAPI types
bash openapi-sync.sh
```

---

## Documentation

- **API Endpoints:** See `API.md`
- **System Architecture:** See `ARCHITECTURE.md`
- **SDK Usage:** See `SDK_USAGE.md`
- **Deployment:** See `DEPLOYMENT.md`
- **Development:** See `CONTRIBUTING.md`

---

## Support

For issues, questions, or suggestions:
1. Check the `Troubleshooting` section above
2. Search existing GitHub issues
3. Create a new issue with:
   - Error message and full traceback
   - Your OS and Python version
   - What you were trying to do
   - Steps to reproduce

