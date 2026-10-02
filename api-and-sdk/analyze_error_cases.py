"""
Analyze the 7 error cases to understand why they failed.
- 2 False Positives: Cases 22, 24 (SAFE marked as FLAGGED)
- 5 False Negatives: Cases 57, 60, 64, 66, 70 (FLAGGED marked as SAFE)
"""

import json
import requests
import time

API_URL = "http://localhost:8000/api/check"

# Error cases
FALSE_POSITIVES = [22, 24]
FALSE_NEGATIVES = [57, 60, 64, 66, 70]

def analyze_case(case_id, case_data):
    """Analyze a single case by calling the API and examining the response."""
    print(f"\n{'='*80}")
    print(f"CASE {case_id}: {case_data['claim'][:80]}...")
    print(f"{'='*80}")
    print(f"Expected: {case_data['expected_label']}")
    print(f"In KB: {case_data['in_kb']}")
    print(f"Section Ref: {case_data.get('section_reference', 'unknown')}")
    
    # Call API
    try:
        response = requests.post(API_URL, json={"text": case_data['claim']})
        if response.status_code != 200:
            print(f"\nERROR: API returned status {response.status_code}")
            print(f"Response: {response.text[:300]}")
            return None
        result = response.json()
        
        # Debug: print raw result
        if not result.get('claims'):
            print(f"\n⚠️  Empty response from API!")
            print(f"Raw response keys: {result.keys()}")
            return None
            
    except Exception as e:
        print(f"\nERROR calling API: {e}")
        print(f"Response status: {response.status_code if 'response' in locals() else 'N/A'}")
        if 'response' in locals():
            print(f"Response text: {response.text[:200]}")
        return None
    
    print(f"\nActual Decision: {result.get('decision', 'N/A')}")
    print(f"Trust Index: {result.get('trust_index', 'N/A')}")
    
    # Show verdict details for each claim
    print(f"\n--- Claims & Verdicts ({len(result.get('claims', []))}) ---")
    for i, (claim, verdict) in enumerate(zip(result.get('claims', []), result.get('verdicts', [])), 1):
        print(f"\n{i}. Claim: {claim.get('text', '')[:70]}...")
        print(f"   Status: {verdict.get('status', 'N/A')}")
        print(f"   Confidence: {verdict.get('confidence', 0) if verdict.get('confidence') is not None else 0:.2f}")
        print(f"   Reasoning: {verdict.get('reasoning', 'N/A')[:80]}...")
        
        # KB match info
        if 'kb_match' in verdict and verdict['kb_match']:
            kb = verdict['kb_match']
            print(f"   KB Match: {kb.get('section', 'N/A')} (score: {kb.get('score', 0):.3f})")
            print(f"   KB Text: {kb.get('text', '')[:60]}...")
    
    return result

def main():
    # Load test cases
    with open('test_cases_70_it_act.json', 'r') as f:
        test_data = json.load(f)
    test_cases = test_data['test_cases']
    
    print("\n" + "="*80)
    print("FALSE POSITIVES ANALYSIS (Expected SAFE, Got FLAGGED)")
    print("="*80)
    
    for case_id in FALSE_POSITIVES:
        case = next(c for c in test_cases if c['id'] == case_id)
        analyze_case(case_id, case)
        time.sleep(1)
    
    print("\n\n" + "="*80)
    print("FALSE NEGATIVES ANALYSIS (Expected FLAGGED, Got SAFE)")
    print("="*80)
    
    for case_id in FALSE_NEGATIVES:
        case = next(c for c in test_cases if c['id'] == case_id)
        analyze_case(case_id, case)
        time.sleep(1)
    
    print("\n\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"False Positives: {len(FALSE_POSITIVES)} cases")
    print(f"False Negatives: {len(FALSE_NEGATIVES)} cases")
    print(f"Total Errors: {len(FALSE_POSITIVES) + len(FALSE_NEGATIVES)} / 70 (10%)")
    print(f"Target: < 5-9% errors for 91-95% accuracy")

if __name__ == "__main__":
    main()
