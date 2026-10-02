"""
Diagnostic script to trace the KB lookup → LLM verification flow.
This will show us WHY the API is calling LLM even for KB claims.
"""
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "detection-engine"))

from shared.schemas import Claim, ClaimType
from stages.kb_lookup import kb_lookup

# Test with a claim that SHOULD be in the KB
test_claims = [
    {
        "text": "Section 66 covers computer related offences punishable with imprisonment up to three years",
        "expected": "Should find in KB (exact match for Section 66)"
    },
    {
        "text": "Section 66A was struck down by the Supreme Court in Shreya Singhal vs Union of India case",
        "expected": "Should find in KB (exact match for Section 66A)"
    },
    {
        "text": "Section 43A covers compensation for failure to protect data",
        "expected": "Should find in KB (exact match for Section 43A)"
    },
    {
        "text": "The IT Act 2000 received presidential assent on 9th June, 2000",
        "expected": "May need semantic search (no specific section)"
    },
]

print("=" * 80)
print("DIAGNOSING KB LOOKUP FLOW")
print("=" * 80)

for i, test_case in enumerate(test_claims, 1):
    print(f"\n{'─' * 80}")
    print(f"TEST {i}: {test_case['text'][:70]}...")
    print(f"Expected: {test_case['expected']}")
    print(f"{'─' * 80}")
    
    # Create a Claim object
    claim = Claim(
        id=f"test_claim_{i}",
        text=test_case['text'],
        type=ClaimType.SECTION_REF,
        span=(0, len(test_case['text']))
    )
    
    # Call kb_lookup
    result = kb_lookup(claim, top_k=3)
    
    print(f"\n📊 KB Lookup Result:")
    print(f"   Hit: {result.hit}")
    print(f"   Best Score: {result.best_score:.4f}")
    print(f"   Threshold: 0.45")
    print(f"   Passages: {len(result.passages)}")
    
    if result.passages:
        print(f"\n📄 Top Passage:")
        top = result.passages[0]
        print(f"   Source: {top.source}")
        print(f"   Score: {top.score:.4f}")
        print(f"   Match Type: {top.metadata.get('match_type', 'unknown')}")
        print(f"   Text Preview: {top.text[:150]}...")
        
        # Check if this would trigger LLM call
        if result.hit:
            print(f"\n✅ Would use KB verdict (NO LLM CALL)")
        else:
            print(f"\n⚠️  Would fall back to LLM web search (USES API KEY)")
            print(f"   Reason: best_score ({result.best_score:.4f}) < threshold (0.45)")
    else:
        print(f"\n❌ No passages found - would fall back to LLM")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
Expected behavior:
1. Claims with section numbers (66, 66A, 43A) → Should get exact match (score 0.95)
2. Exact matches → Should return KB verdict directly (NO LLM call)
3. Only claims NOT in KB → Should use LLM web search

If scores are < 0.45 for KB claims, the problem is:
  - Section regex not matching properly
  - PostgreSQL lookup failing
  - FAISS semantic search not finding sections
""")
