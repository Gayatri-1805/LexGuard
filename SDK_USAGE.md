# SDK Usage Guide

## Python SDK

### Installation

```bash
pip install legal-hallucination-sdk
```

Or install from source:

```bash
pip install -e sdk-python/
```

### Basic Usage

```python
from legal_hallucination_sdk import HallucinationDetectorClient, DetectorAPIError

# Initialize client
client = HallucinationDetectorClient(base_url="http://localhost:8000/api")

# Check for hallucinations
response = client.check(
    text="Section 43A requires compensation for data breach.",
    context="Legal analysis document"
)

# Access results
print(f"Decision: {response['decision']}")           # SAFE, FLAGGED, or ABSTAIN
print(f"Trust Index: {response['trust_index']}")     # 0-1
print(f"Request ID: {response['request_id']}")       # for tracing
print(f"Claims extracted: {len(response['claims'])}")
print(f"Verdicts: {len(response['verdicts'])}")
```

### Check Hallucination

```python
response = client.check(
    text="The burden of proof for data breach is strict liability.",
    context="Optional: system prompt or framing",
    request_id="optional-my-trace-id"  # for your own tracing
)

# Response structure
{
    "request_id": "...",
    "claims": [
        {
            "id": "claim_001",
            "text": "...",
            "type": "SECTION_REF",  # or CASE_CITATION, HOLDING, PROCEDURAL, OTHER
            "span": [0, 60]
        }
    ],
    "verdicts": [
        {
            "claim_id": "claim_001",
            "label": "ENTAILED",  # or CONTRADICTED, NOT_ENOUGH_INFO, LOW_RISK_SKIP
            "evidence": ["Section 43A: ..."],
            "stage_reached": 2,
            "confidence": 0.92
        }
    ],
    "trust_index": 0.92,
    "decision": "SAFE"  # or FLAGGED, ABSTAIN
}
```

### Get Analytics Summary

```python
# Get stats for past 30 days
summary = client.get_summary(days=30)

print(f"Total checks: {summary['total_checks']}")
print(f"Safe: {summary['checks_safe']}, Flagged: {summary['checks_flagged']}, Abstain: {summary['checks_abstain']}")
print(f"Average trust index: {summary['avg_trust_index']}")
print(f"Date range: {summary['date_range']['from']} to {summary['date_range']['to']}")
```

### Get Recent Checks

```python
# Get paginated list of checks
result = client.get_checks(limit=50, offset=0)

print(f"Total checks: {result['total']}")
for check in result['checks']:
    print(f"  {check['request_id']}: {check['decision']} (trust: {check['trust_index']})")

# Pagination example
page_1 = client.get_checks(limit=50, offset=0)
page_2 = client.get_checks(limit=50, offset=50)
page_3 = client.get_checks(limit=50, offset=100)
```

### Get Flagged Checks

```python
# Get checks that need review (decision != SAFE)
flagged = client.get_flagged(limit=100)

print(f"Flagged checks to review: {flagged['total']}")
for check in flagged['flagged_checks']:
    print(f"  {check['request_id']}: {check['decision']}")
```

### Error Handling

```python
from legal_hallucination_sdk import DetectorAPIError

try:
    response = client.check(text="Section 43A...")
except DetectorAPIError as e:
    print(f"API Error {e.status_code}: {e.detail}")
    print(f"Response: {e.response_text}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Context Manager

```python
# Auto-close HTTP connection
with HallucinationDetectorClient(base_url="http://localhost:8000/api") as client:
    response = client.check(text="Section 43A...")
    print(response['decision'])
# Connection closed automatically
```

### Batch Processing

```python
texts = [
    "Section 43A requires compensation.",
    "Privacy is a fundamental right.",
    "Burden of proof is willful negligence."
]

results = []
for text in texts:
    response = client.check(text=text, context="Batch processing")
    results.append({
        'text': text,
        'decision': response['decision'],
        'trust': response['trust_index']
    })

for r in results:
    print(f"{r['text'][:30]}... → {r['decision']} ({r['trust']})")
```

---

## TypeScript SDK

### Installation

```bash
npm install @legal-hallucination/sdk
```

Or build from source:

```bash
cd sdk-npm
npm install
npm run build
```

### Basic Usage

```typescript
import { HallucinationDetectorClient } from '@legal-hallucination/sdk';

const client = new HallucinationDetectorClient('http://localhost:8000/api');

const response = await client.check({
  text: 'Section 43A requires compensation for data breach.',
  context: 'Legal analysis document'
});

console.log(`Decision: ${response.decision}`);         // SAFE, FLAGGED, ABSTAIN
console.log(`Trust Index: ${response.trust_index}`);   // 0-1
console.log(`Claims: ${response.claims.length}`);
```

### Check Hallucination

```typescript
const response = await client.check({
  text: 'The burden of proof for data breach is strict liability.',
  context: 'Optional: system prompt',
  request_id: 'optional-trace-id'
});

// Access results
if (response.decision === 'FLAGGED') {
  console.log('⚠️ Hallucination detected!');
  response.verdicts.forEach(verdict => {
    if (verdict.label === 'CONTRADICTED') {
      console.log(`Contradicted: ${verdict.evidence[0]}`);
    }
  });
} else if (response.decision === 'SAFE') {
  console.log('✓ No hallucinations detected');
} else {
  console.log('? Insufficient evidence');
}
```

### Get Analytics

```typescript
// Summary
const summary = await client.getSummary(30);
console.log(`Checks: ${summary.total_checks}, Avg trust: ${summary.avg_trust_index}`);

// Recent checks
const checks = await client.getChecks(50, 0);
checks.checks.forEach(check => {
  console.log(`${check.request_id}: ${check.decision}`);
});

// Flagged checks
const flagged = await client.getFlagged(50, 0);
console.log(`Flagged: ${flagged.total}`);
```

### Error Handling

```typescript
import { DetectorAPIError } from '@legal-hallucination/sdk';

try {
  const response = await client.check({ text: 'Section 43A...' });
} catch (error) {
  if (error instanceof DetectorAPIError) {
    console.error(`API Error ${error.statusCode}: ${error.detail}`);
  } else {
    console.error('Unexpected error:', error);
  }
}
```

### React Example

```typescript
import { useState } from 'react';
import { HallucinationDetectorClient, DetectorAPIError } from '@legal-hallucination/sdk';

export function HallucinationChecker() {
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const client = new HallucinationDetectorClient('http://localhost:8000/api');

  const handleCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await client.check({ text });
      setResult(response);
    } catch (err) {
      if (err instanceof DetectorAPIError) {
        setError(`API Error: ${err.detail}`);
      } else {
        setError('Failed to check hallucination');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Enter legal text to check..."
      />
      <button onClick={handleCheck} disabled={loading}>
        {loading ? 'Checking...' : 'Check'}
      </button>

      {error && <div style={{ color: 'red' }}>{error}</div>}
      {result && (
        <div>
          <h3>Decision: {result.decision}</h3>
          <p>Trust Index: {result.trust_index.toFixed(2)}</p>
          <p>Claims: {result.claims.length}</p>
          {result.decision === 'FLAGGED' && (
            <ul>
              {result.verdicts
                .filter(v => v.label === 'CONTRADICTED')
                .map(v => (
                  <li key={v.claim_id}>
                    <strong>Contradicted:</strong> {v.evidence[0]}
                  </li>
                ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
```

### Vue Example

```vue
<template>
  <div>
    <textarea
      v-model="text"
      placeholder="Enter legal text to check..."
    />
    <button @click="checkHallucination" :disabled="loading">
      {{ loading ? 'Checking...' : 'Check' }}
    </button>

    <div v-if="error" style="color: red">{{ error }}</div>
    <div v-if="result">
      <h3>Decision: {{ result.decision }}</h3>
      <p>Trust Index: {{ result.trust_index.toFixed(2) }}</p>
      <p>Claims: {{ result.claims.length }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { HallucinationDetectorClient } from '@legal-hallucination/sdk';

const text = ref('');
const result = ref(null);
const loading = ref(false);
const error = ref(null);

const client = new HallucinationDetectorClient('http://localhost:8000/api');

async function checkHallucination() {
  loading.value = true;
  error.value = null;
  try {
    result.value = await client.check({ text: text.value });
  } catch (err) {
    error.value = 'Failed to check hallucination';
  } finally {
    loading.value = false;
  }
}
</script>
```

---

## CLI Tool (Future)

```bash
# Not yet implemented, but planned:
halo-check --file document.txt
halo-check --text "Section 43A..."
halo-check --batch documents/
```

---

## Performance Tips

1. **Reuse client:** Don't create a new client for each request
2. **Batch checks:** Group related checks and process them together
3. **Cache results:** Store trust_index locally for 30 days
4. **Pagination:** Use limit/offset for large analytics queries (don't fetch all at once)
5. **Async/await:** Use async operations in your application

---

## Migration Guide

### From Old API to New SDK

**Before:**
```python
import requests
response = requests.post('http://localhost:8000/api/check', json={'text': '...'})
data = response.json()
```

**After:**
```python
from legal_hallucination_sdk import HallucinationDetectorClient
client = HallucinationDetectorClient('http://localhost:8000/api')
data = client.check(text='...')
```

---

## Testing

### Unit Tests (Python)

```python
import pytest
from legal_hallucination_sdk import HallucinationDetectorClient

@pytest.mark.asyncio
async def test_check_safe():
    client = HallucinationDetectorClient('http://localhost:8000/api')
    response = client.check(text='Section 43A requires data protection.')
    assert response['decision'] in ['SAFE', 'FLAGGED', 'ABSTAIN']
    assert 0 <= response['trust_index'] <= 1
```

### Integration Tests (TypeScript)

```typescript
describe('HallucinationDetectorClient', () => {
  let client: HallucinationDetectorClient;

  beforeAll(() => {
    client = new HallucinationDetectorClient('http://localhost:8000/api');
  });

  it('should check hallucinations', async () => {
    const response = await client.check({
      text: 'Section 43A requires data protection.'
    });
    expect(['SAFE', 'FLAGGED', 'ABSTAIN']).toContain(response.decision);
    expect(response.trust_index).toBeGreaterThanOrEqual(0);
    expect(response.trust_index).toBeLessThanOrEqual(1);
  });
});
```

