# FastAPI Service & SDKs — Run Instructions

## Overview

The hallucination detection API and Python/TypeScript SDKs are now ready to test.

**Components:**
- **API**: `api/main.py` with routes for checking hallucinations and analytics
- **SDK Python**: `sdk-python/` with `HallucinationDetectorClient` 
- **SDK TypeScript**: `sdk-npm/` with generated types from OpenAPI schema
- **Analytics**: In-process logging to Postgres `check_logs` table
- **Pipeline**: Stub that returns realistic CheckResponse (swap for Person A's real pipeline)

---

## Step 1: Install Dependencies

```bash
cd d:\projects\HALO\legal-hallucination-detector\api-and-sdk
pip install -q -r requirements.txt
```

Expected output: No errors, all packages installed silently.

---

## Step 2: Initialize Analytics Database

```bash
python -m api.analytics.init_db
```

Expected output:
```
Creating analytics tables...
✓ Database initialized
```

This creates the `check_logs` table in Postgres for analytics persistence.

---

## Step 3: Start the API Locally

Open a **new terminal** and run:

```bash
cd d:\projects\HALO\legal-hallucination-detector\api-and-sdk
python -m uvicorn api.main:app --reload --port 8000
```

Expected output (after ~2 seconds):
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

**Keep this terminal open** — the API will run in the foreground.

---

## Step 4: Verify Health Endpoint (New Terminal)

Open a **second terminal** and run:

```bash
curl http://localhost:8000/health
```

Expected output:
```json
{"status":"ok"}
```

---

## Step 5: Test POST /check Endpoint

```bash
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Section 43A requires data protection measures.",
    "context": "Legal analysis"
  }'
```

Expected output (CheckResponse with claims, verdicts, trust_index, decision):
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "claims": [
    {
      "id": "claim_001",
      "text": "Section 43A of the IT Act requires data protection measures.",
      "type": "SECTION_REF",
      "span": [0, 60]
    }
  ],
  "verdicts": [
    {
      "claim_id": "claim_001",
      "label": "ENTAILED",
      "evidence": ["Section 43A: Compensation for failure to protect data..."],
      "stage_reached": 2,
      "confidence": 0.92
    }
  ],
  "trust_index": 0.92,
  "decision": "SAFE",
  "created_at": "2026-09-04T15:30:45.123456+00:00"
}
```

---

## Step 6: Verify Analytics Was Logged

```bash
curl http://localhost:8000/api/analytics/checks
```

Expected output: Recent checks list with your test check visible:
```json
{
  "total": 1,
  "checks": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "trust_index": 0.92,
      "decision": "SAFE",
      "created_at": "2026-09-04T15:30:45Z"
    }
  ]
}
```

---

## Step 7: Test All Analytics Endpoints

```bash
# Summary stats
curl http://localhost:8000/api/analytics/summary?days=30

# Flagged checks (empty if none)
curl http://localhost:8000/api/analytics/flagged
```

---

## Step 8: Run Comprehensive Test Script (Python)

From the **second terminal** (not the API terminal):

```bash
cd d:\projects\HALO\legal-hallucination-detector\api-and-sdk
python test_api.py
```

Expected output: All 5 tests pass with ✓ marks.

---

## Step 9: Generate OpenAPI Schema & TypeScript Types

```bash
cd d:\projects\HALO\legal-hallucination-detector\api-and-sdk
bash openapi-sync.sh
```

**Note:** On Windows, you may need WSL or Git Bash. Alternative (Windows Command Prompt):

```cmd
python -c "import json; from api.main import app; schema = app.openapi(); f = open('openapi.json', 'w'); json.dump(schema, f, indent=2); f.close(); print('✓ openapi.json created')"
npx openapi-typescript openapi.json -o sdk-npm/src/generated-types.ts
```

Expected output:
- `openapi.json` created with full OpenAPI 3.0 schema
- `sdk-npm/src/generated-types.ts` auto-generated with TypeScript interfaces

---

## Step 10: Build NPM SDK

```bash
cd d:\projects\HALO\legal-hallucination-detector\api-and-sdk\sdk-npm
npm install
npm run build
```

Expected output:
```
dist/client.js
dist/client.d.ts
```

---

## Step 11: Test Python SDK

```bash
python -c "
from legal_hallucination_sdk import HallucinationDetectorClient, DetectorAPIError

client = HallucinationDetectorClient(base_url='http://localhost:8000/api')

# Test check endpoint
response = client.check(text='Section 43A requires data protection.', context='Legal')
print(f'Decision: {response[\"decision\"]}')
print(f'Trust: {response[\"trust_index\"]}')

# Test analytics
summary = client.get_summary(days=30)
print(f'Total checks: {summary[\"total_checks\"]}')
print(f'Avg trust: {summary[\"avg_trust_index\"]}')

print('✓ Python SDK works!')
"
```

---

## Step 12: Test TypeScript SDK (if Node.js available)

Create `test-ts-client.ts`:

```typescript
import { HallucinationDetectorClient } from './sdk-npm/dist/client';

async function testTSClient() {
  const client = new HallucinationDetectorClient('http://localhost:8000/api');
  
  const response = await client.check({
    text: 'Section 43A requires data protection.',
    context: 'Legal analysis'
  });
  
  console.log(`Decision: ${response.decision}`);
  console.log(`Trust: ${response.trust_index}`);
  
  const summary = await client.getSummary(30);
  console.log(`Total checks: ${summary.total_checks}`);
  console.log('✓ TypeScript SDK works!');
}

testTSClient();
```

Run:
```bash
npx tsx test-ts-client.ts
```

---

## Troubleshooting

### API won't start: `ModuleNotFoundError`
- Ensure you've run `pip install -q -r requirements.txt` first
- Check that Python is in PATH and the virtual env is activated

### `GET /health` fails
- Check that uvicorn is running (see Step 3 terminal)
- Verify port 8000 is available: `netstat -ano | findstr :8000`
- Try a different port: `--port 8001`

### `POST /check` returns 500
- Check the API terminal for error messages
- Ensure `api/pipeline_stub.py` is importable
- Verify shared/schemas.py is accessible

### Database errors
- Ensure DATABASE_URL is set in `.env`
- Run `python -m api.analytics.init_db` again
- Check Postgres connection: `psql -c "SELECT version();"`

### OpenAPI schema generation fails
- Ensure the FastAPI app starts without errors first
- On Windows, use WSL, Git Bash, or the Python alternative command above

---

## Integration with Person A's Pipeline

When Person A completes `detection-engine/pipeline.py`, swap the stub:

**In `api/routes/check.py`, change:**

```python
# OLD
from api.pipeline_stub import check as PIPELINE_CHECK_FN

# NEW
from detection_engine.pipeline import check as PIPELINE_CHECK_FN
```

No other changes needed — the interface is compatible.

---

## Next: Person C's Dashboard

The analytics endpoints (`/analytics/summary`, `/analytics/checks`, `/analytics/flagged`) are ready for Person C's dashboard to consume.

See `api/routes/analytics.py` for the full endpoint contract.

---

## Summary

✓ API running on `http://localhost:8000`  
✓ Python SDK in `sdk-python/` (pip installable)  
✓ TypeScript SDK in `sdk-npm/` (npm installable)  
✓ Analytics logging to Postgres  
✓ OpenAPI schema + generated types  
✓ Stub pipeline (ready for integration with Person A)  

**You're ready to build!**
