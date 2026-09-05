"""
Test script for FastAPI hallucination detection service.

Tests all endpoints with sample requests.
Run: python test_api.py
"""

import httpx
import json
import time
from datetime import datetime


BASE_URL = "http://localhost:8000/api"

print("=" * 70)
print("Testing Hallucination Detection API")
print("=" * 70)
print()

# Test 1: Health endpoint
print("Test 1: GET /health")
print("-" * 70)
try:
    response = httpx.get("http://localhost:8000/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print("✓ Health check passed\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    exit(1)

# Test 2: POST /check with sample text
print("Test 2: POST /check with sample text")
print("-" * 70)
try:
    payload = {
        "text": "Section 43A requires data protection measures. Privacy is a fundamental right.",
        "context": "Legal analysis"
    }
    response = httpx.post(f"{BASE_URL}/check", json=payload)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Response shape:")
    print(f"  - claims: {len(data.get('claims', []))} items")
    print(f"  - verdicts: {len(data.get('verdicts', []))} items")
    print(f"  - trust_index: {data.get('trust_index', 'N/A')}")
    print(f"  - decision: {data.get('decision', 'N/A')}")
    print(f"  - request_id: {data.get('request_id', 'N/A')}")
    
    request_id = data.get('request_id')
    print("✓ Check passed\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    exit(1)

# Wait for background task to complete
print("Waiting for analytics to be recorded...")
time.sleep(2)

# Test 3: GET /analytics/summary
print("Test 3: GET /analytics/summary")
print("-" * 70)
try:
    response = httpx.get(f"{BASE_URL}/analytics/summary?days=30")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Summary:")
    print(f"  - total_checks: {data.get('total_checks', 0)}")
    print(f"  - checks_safe: {data.get('checks_safe', 0)}")
    print(f"  - checks_flagged: {data.get('checks_flagged', 0)}")
    print(f"  - avg_trust_index: {data.get('avg_trust_index', 0)}")
    print("✓ Analytics summary passed\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    exit(1)

# Test 4: GET /analytics/checks
print("Test 4: GET /analytics/checks")
print("-" * 70)
try:
    response = httpx.get(f"{BASE_URL}/analytics/checks?limit=10")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Checks:")
    print(f"  - total: {data.get('total', 0)}")
    print(f"  - items: {len(data.get('checks', []))}")
    if data.get('checks'):
        for check in data.get('checks', [])[:3]:
            print(f"    • {check.get('request_id')}: {check.get('decision')} ({check.get('trust_index')})")
    print("✓ Checks list passed\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    exit(1)

# Test 5: GET /analytics/flagged
print("Test 5: GET /analytics/flagged")
print("-" * 70)
try:
    response = httpx.get(f"{BASE_URL}/analytics/flagged?limit=10")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(f"Flagged checks:")
    print(f"  - total: {data.get('total', 0)}")
    print(f"  - items: {len(data.get('flagged_checks', []))}")
    print("✓ Flagged checks passed\n")
except Exception as e:
    print(f"✗ Failed: {e}\n")
    exit(1)

print("=" * 70)
print("✓ All tests passed!")
print("=" * 70)
print()
print("Next steps:")
print("  1. Run openapi-sync.sh to generate OpenAPI schema and TS types")
print("  2. Build npm package: cd sdk-npm && npm install && npm run build")
print("  3. Test Python SDK: python -c \"from legal_hallucination_sdk import HallucinationDetectorClient; ...\"")
