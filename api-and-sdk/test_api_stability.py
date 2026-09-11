#!/usr/bin/env python
"""
Quick API Stability Test
Test 10 requests to ensure API can handle load
"""
import requests
import time

def test_api_stability():
    print("Testing API stability with 10 requests...")
    
    test_texts = [
        "Section 43 provides for compensation.",
        "Section 66 punishes hacking.",
        "Section 67 deals with obscene material.",
        "Section 43A requires data protection.",
        "Section 69 empowers government interception.",
        "Section 79 provides safe harbor.",
        "Section 66F punishes cyber terrorism.",
        "Section 72 punishes breach of confidentiality.",
        "Section 43 provides imprisonment for 5 years.",  # Hallucination
        "Section 10A validates electronic contracts."
    ]
    
    success_count = 0
    error_count = 0
    total_time = 0
    
    for i, text in enumerate(test_texts, 1):
        try:
            start = time.time()
            response = requests.post(
                "http://localhost:8000/api/check",
                json={"text": text, "context": "Test", "request_id": f"stability_test_{i}"},
                timeout=30
            )
            elapsed = time.time() - start
            total_time += elapsed
            
            if response.status_code == 200:
                data = response.json()
                decision = data.get('decision', 'UNKNOWN')
                trust = data.get('trust_index', 0)
                print(f"  {i}/10: ✓ {decision} (trust: {trust:.3f}, {elapsed:.2f}s)")
                success_count += 1
            else:
                print(f"  {i}/10: ✗ HTTP {response.status_code}")
                error_count += 1
                
        except Exception as e:
            print(f"  {i}/10: ✗ Error: {e}")
            error_count += 1
    
    print(f"\n📊 Results:")
    print(f"  Success: {success_count}/10")
    print(f"  Errors: {error_count}/10")
    print(f"  Avg time: {total_time/10:.2f}s")
    print(f"  Total time: {total_time:.2f}s")
    
    if success_count >= 9:
        print("\n✅ API is STABLE and ready for 250-case test!")
        return True
    else:
        print("\n⚠️ API has stability issues. Check logs.")
        return False

if __name__ == "__main__":
    stable = test_api_stability()
    exit(0 if stable else 1)
