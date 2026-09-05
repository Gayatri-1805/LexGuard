# API Documentation

## Base URL

```
http://localhost:8000/api
```

For production, replace with your deployment URL.

---

## Endpoints

### 1. Check Hallucination

**Endpoint:** `POST /api/check`

**Description:** Analyze LLM output for hallucinations using the detection pipeline.

**Request Body:**

```json
{
  "text": "Section 43A requires data protection measures.",
  "context": "Optional: prompt or framing that produced the text",
  "request_id": "Optional: your own request identifier for tracing"
}
```

**Request Schema:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | string | ✓ | LLM output to check (e.g., legal analysis, case summary) |
| context | string | ✗ | Optional prompt or system message that generated the text |
| request_id | string | ✗ | Your own unique ID for tracing; if omitted, server generates one |

**Response (200 OK):**

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
      "evidence": [
        "Section 43A: Compensation for failure to protect data..."
      ],
      "stage_reached": 2,
      "confidence": 0.92
    }
  ],
  "trust_index": 0.92,
  "decision": "SAFE",
  "created_at": "2026-09-05T11:28:28.631281Z"
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| request_id | string | Unique identifier for this check (for tracing) |
| claims | array | List of extracted claims from input text |
| claims[].id | string | Claim identifier (e.g., "claim_001") |
| claims[].text | string | The atomic claim text |
| claims[].type | string | Claim type: SECTION_REF, CASE_CITATION, HOLDING, PROCEDURAL, OTHER |
| claims[].span | array[2] | Character offsets [start, end] in original text |
| verdicts | array | Verdict for each claim |
| verdicts[].claim_id | string | Reference to claims[].id |
| verdicts[].label | string | ENTAILED, CONTRADICTED, NOT_ENOUGH_INFO, or LOW_RISK_SKIP |
| verdicts[].evidence | array | Retrieved KB passages supporting this verdict |
| verdicts[].stage_reached | int | Pipeline stage that produced this verdict (1-4) |
| verdicts[].confidence | float | Confidence score (0-1) if available |
| trust_index | float | Aggregate hallucination risk (0=risky, 1=safe) |
| decision | string | Final decision: SAFE, FLAGGED, or ABSTAIN |
| created_at | string | UTC timestamp when check completed |

**Error Response (500):**

```json
{
  "detail": "Hallucination detection failed: [error message]"
}
```

**Example Request (curl):**

```bash
curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Section 43A requires compensation for data breach.",
    "context": "Legal analysis"
  }'
```

**Example Request (Python SDK):**

```python
from legal_hallucination_sdk import HallucinationDetectorClient

client = HallucinationDetectorClient('http://localhost:8000/api')
response = client.check(
    text="Section 43A requires compensation for data breach.",
    context="Legal analysis"
)
print(response['decision'])       # SAFE, FLAGGED, or ABSTAIN
print(response['trust_index'])    # 0-1
print(response['claims'])         # [...]
print(response['verdicts'])       # [...]
```

**Example Request (TypeScript SDK):**

```typescript
import { HallucinationDetectorClient } from './sdk-npm/dist/client';

const client = new HallucinationDetectorClient('http://localhost:8000/api');
const response = await client.check({
  text: 'Section 43A requires compensation for data breach.',
  context: 'Legal analysis'
});

console.log(response.decision);       // SAFE, FLAGGED, or ABSTAIN
console.log(response.trust_index);    // 0-1
console.log(response.claims);         // [...]
console.log(response.verdicts);       // [...]
```

---

### 2. Get Analytics Summary

**Endpoint:** `GET /api/analytics/summary`

**Description:** Get aggregate statistics for the past N days.

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| days | integer | 30 | 1-365 | Number of days to look back |

**Response (200 OK):**

```json
{
  "total_checks": 1234,
  "checks_safe": 1000,
  "checks_flagged": 200,
  "checks_abstain": 34,
  "avg_trust_index": 0.81,
  "date_range": {
    "from": "2026-08-06",
    "to": "2026-09-05"
  }
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| total_checks | integer | Total checks processed in this period |
| checks_safe | integer | Checks with decision SAFE |
| checks_flagged | integer | Checks with decision FLAGGED |
| checks_abstain | integer | Checks with decision ABSTAIN |
| avg_trust_index | float | Average trust_index across all checks |
| date_range.from | string | Start date (ISO 8601) |
| date_range.to | string | End date (ISO 8601) |

**Example Request (curl):**

```bash
curl http://localhost:8000/api/analytics/summary?days=30
```

**Example Request (Python SDK):**

```python
summary = client.get_summary(days=30)
print(f"Total checks: {summary['total_checks']}")
print(f"Avg trust: {summary['avg_trust_index']}")
print(f"Safe: {summary['checks_safe']}, Flagged: {summary['checks_flagged']}")
```

**Example Request (TypeScript SDK):**

```typescript
const summary = await client.getSummary(30);
console.log(`Total checks: ${summary.total_checks}`);
console.log(`Avg trust: ${summary.avg_trust_index}`);
```

---

### 3. Get Recent Checks

**Endpoint:** `GET /api/analytics/checks`

**Description:** Get paginated list of recent checks.

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| limit | integer | 50 | 1-500 | Max results per page |
| offset | integer | 0 | ≥ 0 | Pagination offset |

**Response (200 OK):**

```json
{
  "total": 1234,
  "checks": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "trust_index": 0.92,
      "decision": "SAFE",
      "created_at": "2026-09-05T11:28:28Z"
    },
    {
      "request_id": "660e8400-e29b-41d4-a716-446655440001",
      "trust_index": 0.18,
      "decision": "FLAGGED",
      "created_at": "2026-09-05T10:15:42Z"
    }
  ]
}
```

**Response Schema:**

| Field | Type | Description |
|-------|------|-------------|
| total | integer | Total checks (for pagination) |
| checks | array | Array of recent checks (newest first) |
| checks[].request_id | string | Unique check identifier |
| checks[].trust_index | float | Trust score (0-1) |
| checks[].decision | string | SAFE, FLAGGED, or ABSTAIN |
| checks[].created_at | string | UTC timestamp |

**Example Request (curl):**

```bash
curl "http://localhost:8000/api/analytics/checks?limit=10&offset=0"
```

**Example Request (Python SDK):**

```python
result = client.get_checks(limit=10, offset=0)
print(f"Total checks: {result['total']}")
for check in result['checks']:
    print(f"  {check['request_id']}: {check['decision']} (trust: {check['trust_index']})")
```

---

### 4. Get Flagged Checks

**Endpoint:** `GET /api/analytics/flagged`

**Description:** Get checks with decision != SAFE (for review dashboard).

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| limit | integer | 50 | 1-500 | Max results per page |
| offset | integer | 0 | ≥ 0 | Pagination offset |

**Response (200 OK):**

```json
{
  "total": 234,
  "flagged_checks": [
    {
      "request_id": "550e8400-e29b-41d4-a716-446655440000",
      "trust_index": 0.18,
      "decision": "FLAGGED",
      "created_at": "2026-09-05T10:20:15Z"
    }
  ]
}
```

**Response Schema:** Same as `/api/analytics/checks` but field is `flagged_checks`.

**Example Request (curl):**

```bash
curl "http://localhost:8000/api/analytics/flagged?limit=50"
```

**Example Request (Python SDK):**

```python
flagged = client.get_flagged(limit=50)
print(f"Total flagged: {flagged['total']}")
for check in flagged['flagged_checks']:
    print(f"  Review: {check['request_id']} ({check['decision']})")
```

---

### 5. Health Check

**Endpoint:** `GET /health`

**Description:** Simple uptime check. Returns 200 OK if API is running.

**Response (200 OK):**

```json
{
  "status": "ok"
}
```

**Example Request (curl):**

```bash
curl http://localhost:8000/health
```

---

## Data Models

### Claim

```json
{
  "id": "claim_001",
  "text": "Section 43A of the IT Act requires data protection measures.",
  "type": "SECTION_REF",
  "span": [0, 60]
}
```

**Types:**
- `SECTION_REF` — Reference to a statute section (e.g., "Section 43A")
- `CASE_CITATION` — Case law citation (e.g., "Miranda v. Arizona")
- `HOLDING` — Legal holding or principle (e.g., "Privacy is a fundamental right")
- `PROCEDURAL` — Procedural rule (e.g., "Burden of proof rests with plaintiff")
- `OTHER` — Uncategorized claim

### Verdict

```json
{
  "claim_id": "claim_001",
  "label": "ENTAILED",
  "evidence": ["Section 43A: Compensation for failure to protect data..."],
  "stage_reached": 2,
  "confidence": 0.92
}
```

**Labels:**
- `ENTAILED` — Claim is supported by evidence (not hallucinated)
- `CONTRADICTED` — Claim is refuted by evidence (hallucinated)
- `NOT_ENOUGH_INFO` — Insufficient evidence to decide
- `LOW_RISK_SKIP` — Claim is non-falsifiable (filtered at Stage 1)

### Decision

```
SAFE     — No hallucinations detected; trust_index >= threshold
FLAGGED  — Hallucinations detected; trust_index < threshold
ABSTAIN  — Mixed evidence; insufficient confidence to decide
```

---

## Error Handling

**HTTP Status Codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid JSON, missing required field) |
| 422 | Validation error (type mismatch, out of range) |
| 500 | Server error (pipeline failed, DB error) |

**Error Response Format:**

```json
{
  "detail": "Human-readable error message"
}
```

**Example:**

```bash
$ curl -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{"text": ""}'

{
  "detail": "text must not be empty"
}
```

---

## Rate Limiting

Currently **no rate limiting** (development mode). Before production, add:
- 100 requests/minute per IP
- 1000 requests/minute per API key
- Exponential backoff on 429 (Too Many Requests)

---

## Pagination

Use `limit` and `offset` for paginating results:

```bash
# Get first 50 checks
GET /api/analytics/checks?limit=50&offset=0

# Get next page
GET /api/analytics/checks?limit=50&offset=50

# Get next page
GET /api/analytics/checks?limit=50&offset=100
```

---

## OpenAPI/Swagger

Interactive API documentation available at:

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc (alternative view)
```

Download OpenAPI schema:

```
http://localhost:8000/openapi.json
```

---

## Response Time Expectations

| Endpoint | Latency (p95) | Notes |
|----------|--------------|-------|
| `/check` | 400-500ms | Includes pipeline stages 0-4; DB logging is async |
| `/analytics/summary` | 50ms | Single aggregation query |
| `/analytics/checks` | 100ms | Index scan on created_at |
| `/analytics/flagged` | 100ms | Index scan on decision |
| `/health` | <1ms | In-memory check |

---

## Versioning

API version: **v0.1.0** (development)

No breaking changes expected until v1.0.0. When major version changes occur, old versions will be supported for 6 months.

---

## Support

For API issues, check:
1. Error message in response body
2. API server logs (stdout when running)
3. `ARCHITECTURE.md` for system design
4. `TROUBLESHOOTING.md` (in GETTING_STARTED.md)

