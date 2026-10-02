"""
Quick test to verify the fixes are working
"""
import requests
import json

API_URL = "http://localhost:8000/api/check"

# Test case that should be FLAGGED (Section 43 is civil, not criminal)
test_case = {
    "text": "Section 43 of the Information Technology Act prescribes mandatory imprisonment of 5 to 10 years for data breaches.",
    "context": "fix_verification_test"
}

print("🧪 Testing Single Case to Verify Fixes")
print("=" * 60)
print(f"Text: {test_case['text']}")
print("\nExpected: FLAGGED (Section 43 is civil liability, not criminal)")
print("\nSending request...")

try:
    response = requests.post(API_URL, json=test_case, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ Response received!")
        print(f"   Decision: {result['decision']}")
        print(f"   Trust Index: {result['trust_index']}")
        print(f"   Claims: {len(result.get('claims', []))}")
        print(f"   Verdicts: {len(result.get('verdicts', []))}")
        
        if result.get('verdicts'):
            print("\n📋 Verdict Details:")
            for i, verdict in enumerate(result['verdicts'], 1):
                print(f"   {i}. Label: {verdict['label']}")
                print(f"      Confidence: {verdict.get('confidence', 'N/A')}")
                if verdict.get('reasoning'):
                    print(f"      Reasoning: {verdict['reasoning'][:100]}...")
        
        # Check if fix worked
        print("\n" + "=" * 60)
        if result['decision'] == 'FLAGGED':
            print("✅ SUCCESS! System correctly flagged the hallucination")
        elif result['decision'] == 'SAFE':
            print("❌ ISSUE: System marked as SAFE (should be FLAGGED)")
            print("   This means LLM fallback may still have issues")
        else:
            print(f"⚠️ UNCERTAIN: Decision is {result['decision']}")
            
    else:
        print(f"\n❌ Error: HTTP {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n❌ Cannot connect to API!")
    print("   Make sure the server is running: python run_api.py")
except Exception as e:
    print(f"\n❌ Error: {e}")
