#!/usr/bin/env python
"""
Debug Verdict Labels and KB Hits
=================================
Check what verdict labels are actually being returned
"""

import requests
import json

# Test with a simple case
test_text = "Section 66 of the Information Technology Act, 2000 deals exclusively with cyber terrorism."

print("🔍 Testing single case to see actual verdict labels...")
print(f"Text: {test_text}\n")

response = requests.post(
    "http://localhost:8000/api/check",
    json={"text": test_text, "context": "Test"},
    timeout=120
)

if response.status_code == 200:
    data = response.json()
    
    print(f"✅ Response received!")
    print(f"Decision: {data['decision']}")
    print(f"Trust Index: {data['trust_index']}")
    print(f"Number of claims: {len(data['claims'])}")
    print(f"Number of verdicts: {len(data['verdicts'])}\n")
    
    print("📋 Detailed Claims and Verdicts:\n")
    for i, (claim, verdict) in enumerate(zip(data['claims'], data['verdicts']), 1):
        print(f"Claim {i}:")
        print(f"  Text: {claim['text']}")
        print(f"  Type: {claim['type']}")
        
        print(f"  Verdict:")
        print(f"    Label: {verdict['label']}")
        print(f"    Confidence: {verdict.get('confidence', 'N/A')}")
        print(f"    Stage Reached: {verdict['stage_reached']}")
        print(f"    Evidence: {verdict.get('evidence', [])[:100] if verdict.get('evidence') else 'None'}...")
        print(f"    Reasoning: {verdict.get('reasoning', 'N/A')[:100]}...")
        print()
    
    print("\n🔍 Verdict Label Summary:")
    verdict_labels = [v['label'] for v in data['verdicts']]
    for label in set(verdict_labels):
        count = verdict_labels.count(label)
        print(f"  {label}: {count}")
    
    print("\n📊 KB Hit Analysis:")
    kb_supported = sum(1 for v in data['verdicts'] if v['label'] in ['ENTAILED', 'SUPPORTED'])
    kb_contradicted = sum(1 for v in data['verdicts'] if v['label'] == 'CONTRADICTED')
    kb_unverifiable = sum(1 for v in data['verdicts'] if v['label'] == 'UNVERIFIABLE')
    kb_partial = sum(1 for v in data['verdicts'] if v['label'] == 'PARTIALLY_SUPPORTED')
    
    print(f"  SUPPORTED/ENTAILED (KB Hits): {kb_supported}")
    print(f"  CONTRADICTED: {kb_contradicted}")
    print(f"  PARTIALLY_SUPPORTED: {kb_partial}")
    print(f"  UNVERIFIABLE: {kb_unverifiable}")
    
    # Save full response for inspection
    with open('verdict_debug_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print("\n💾 Full response saved to: verdict_debug_response.json")
    
else:
    print(f"❌ Error: HTTP {response.status_code}")
    print(response.text)
