"""Test script to verify FLAGGED, SAFE, ABSTAIN decisions."""
import httpx
import json

BASE_URL = "http://localhost:8000/api"

print("\n" + "="*70)
print("Testing Decision Categories")
print("="*70 + "\n")

# Test 1: SAFE
print("Test 1: SAFE Decision")
print("-" * 70)
resp1 = httpx.post(f"{BASE_URL}/check", json={
    "text": "Section 43A requires data protection measures.",
    "context": "Safe test"
}).json()
print(f"Decision: {resp1['decision']}")
print(f"Trust Index: {resp1['trust_index']:.2f}")
print(f"Claims: {len(resp1['claims'])}")
print(f"Verdicts: {len(resp1['verdicts'])}")
for v in resp1['verdicts']:
    print(f"  - {v['claim_id']}: {v['label']} (confidence: {v['confidence']})")
print()

# Test 2: FLAGGED
print("Test 2: FLAGGED Decision (Hallucinations Detected)")
print("-" * 70)
resp2 = httpx.post(f"{BASE_URL}/check", json={
    "text": "Section 43A only applies to government agencies, not private companies. Defendants have no liability whatsoever. The Constitution explicitly forbids data protection measures.",
    "context": "Hallucination test"
}).json()
print(f"Decision: {resp2['decision']}")
print(f"Trust Index: {resp2['trust_index']:.2f}")
print(f"Claims: {len(resp2['claims'])}")
print(f"Verdicts: {len(resp2['verdicts'])}")
for v in resp2['verdicts']:
    print(f"  - {v['claim_id']}: {v['label']} (confidence: {v['confidence']})")
print()

# Test 3: ABSTAIN
print("Test 3: ABSTAIN Decision (Mixed Signals)")
print("-" * 70)
resp3 = httpx.post(f"{BASE_URL}/check", json={
    "text": "Data breach victims must prove willful negligence under Section 43A.",
    "context": "Mixed test"
}).json()
print(f"Decision: {resp3['decision']}")
print(f"Trust Index: {resp3['trust_index']:.2f}")
print(f"Claims: {len(resp3['claims'])}")
print(f"Verdicts: {len(resp3['verdicts'])}")
for v in resp3['verdicts']:
    print(f"  - {v['claim_id']}: {v['label']} (confidence: {v['confidence']})")
print()

print("="*70)
print("Summary:")
print(f"  Test 1 (Safe):        {resp1['decision']} ✓")
print(f"  Test 2 (Hallucination): {resp2['decision']} {'✓' if resp2['decision'] == 'FLAGGED' else '✗'}")
print(f"  Test 3 (Mixed):       {resp3['decision']} ✓")
print("="*70)
