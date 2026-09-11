#!/usr/bin/env python
"""
Analyze problematic test cases to understand inconsistencies
"""

import requests
import json

test_cases = [
    {
        "name": "Section 43 (hallucinated)",
        "text": "Section 43 of the Information Technology Act, 2000 provides that a person who accesses a computer without permission is automatically sentenced to imprisonment for up to five years and a fine of up to ten lakh rupees. The section also empowers the police to arrest the offender without a warrant.",
        "expected": "FLAGGED"
    },
    {
        "name": "Section 66 (hallucinated)",  
        "text": "Section 66 of the Information Technology Act, 2000 deals exclusively with cyber terrorism. It provides that anyone who threatens India's sovereignty through a computer network shall receive imprisonment for life as the mandatory punishment, without any requirement of dishonest or fraudulent intent.",
        "expected": "FLAGGED"
    },
    {
        "name": "Section 67 (partially wrong)",
        "text": "Section 67 of the Information Technology Act, 2000 punishes the publishing or transmitting of obscene material in electronic form. On the first conviction, the punishment may extend to three years' imprisonment and a fine up to five lakh rupees. For a second or subsequent conviction, imprisonment may extend to seven years and the fine may extend to ten lakh rupees.",
        "expected": "ABSTAIN"
    }
]

print("🔍 Analyzing Problematic Cases\n")
print("=" * 80)

for i, case in enumerate(test_cases, 1):
    print(f"\n{i}. {case['name']}")
    print(f"   Expected: {case['expected']}")
    print("-" * 80)
    
    response = requests.post(
        "http://localhost:8000/api/check",
        json={"text": case['text'], "context": "Analysis"},
        timeout=120
    )
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"   ✅ Result: {data['decision']} (Trust: {data['trust_index']:.3f})")
        print(f"   Claims: {len(data['claims'])}")
        
        for j, (claim, verdict) in enumerate(zip(data['claims'], data['verdicts']), 1):
            print(f"\n   Claim {j}: {claim['text'][:80]}...")
            print(f"      Citation: {claim.get('citation', 'None')}")
            print(f"      Verdict: {verdict['label']} (conf: {verdict.get('confidence', 'N/A')})")
            print(f"      Stage: {verdict['stage_reached']}")
            
            if verdict.get('reasoning'):
                print(f"      Reasoning: {verdict['reasoning'][:150]}...")
            
            # Check if evidence was found
            evidence = verdict.get('evidence', [])
            if evidence:
                print(f"      Evidence found: {len(evidence)} passages")
                print(f"      First evidence: {evidence[0][:100]}...")
            else:
                print(f"      ❌ NO EVIDENCE FOUND")
        
        # Save detailed response
        filename = f"analysis_{i}_{case['name'].replace(' ', '_').replace('(', '').replace(')', '')}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\n   💾 Saved to: {filename}")
    else:
        print(f"   ❌ Error: HTTP {response.status_code}")

print("\n" + "=" * 80)
print("\n🔍 Analysis Summary:")
print("Check the generated JSON files for detailed verdict reasoning and evidence")
