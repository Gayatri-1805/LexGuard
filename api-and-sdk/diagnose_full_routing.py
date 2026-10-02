"""
Diagnostic script to test the FULL routing from claim → verdict.
This simulates what happens in the actual API endpoint.
"""
import sys
from pathlib import Path

# Add project paths
_API_SDK_ROOT = Path(__file__).resolve().parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from shared.schemas import Claim, ClaimType
from stages.kb_lookup import kb_lookup
from api.routes.check import _has_relevant_info, _kb_direct_verdict

# Test with a claim that SHOULD be in the KB
test_claims = [
    "Section 66 covers computer related offences punishable with imprisonment up to three years",
    "Section 66A was struck down by the Supreme Court in Shreya Singhal vs Union of India case",
    "Section 43A covers compensation for failure to protect data",
]

print("=" * 80)
print("DIAGNOSING FULL ROUTING: KB LOOKUP → _has_relevant_info → _kb_direct_verdict")
print("=" * 80)

for i, claim_text in enumerate(test_claims, 1):
    print(f"\n{'─' * 80}")
    print(f"TEST {i}: {claim_text[:70]}...")
    print(f"{'─' * 80}")
    
    # Create a Claim object
    claim = Claim(
        id=f"test_claim_{i}",
        text=claim_text,
        type=ClaimType.SECTION_REF,
        span=(0, len(claim_text))
    )
    
    # Step 1: KB Lookup
    kb_result = kb_lookup(claim, top_k=3)
    print(f"\n📊 Step 1: KB Lookup")
    print(f"   Hit: {kb_result.hit}")
    print(f"   Best Score: {kb_result.best_score:.4f}")
    print(f"   Top Source: {kb_result.passages[0].source if kb_result.passages else 'N/A'}")
    print(f"   Match Type: {kb_result.passages[0].metadata.get('match_type', 'unknown') if kb_result.passages else 'N/A'}")
    
    if not kb_result.hit:
        print(f"\n❌ KB miss - would call LLM")
        continue
    
    # Step 2: Check relevance
    is_relevant = _has_relevant_info(claim, kb_result)
    print(f"\n📊 Step 2: _has_relevant_info")
    print(f"   Relevant: {is_relevant}")
    
    if not is_relevant:
        print(f"\n⚠️  Passage deemed irrelevant - would call LLM")
        continue
    
    # Step 3: Get KB direct verdict
    verdict = _kb_direct_verdict(claim, kb_result)
    print(f"\n📊 Step 3: _kb_direct_verdict")
    
    if verdict is None:
        print(f"   Verdict: None (off-topic)")
        print(f"\n⚠️  KB returned None verdict - would call LLM")
    else:
        print(f"   Verdict: {verdict.label.value}")
        print(f"   Confidence: {verdict.confidence:.3f}")
        print(f"   Reasoning: {verdict.reasoning[:100]}...")
        print(f"\n✅ Would use KB verdict (NO LLM CALL)")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print("""
If any test shows "would call LLM", the issue is in one of these steps:
1. KB lookup returning hit=False (threshold too high)
2. _has_relevant_info returning False (relevance check too strict)
3. _kb_direct_verdict returning None (off-topic detection too strict)

Expected: All 3 tests should show "✅ Would use KB verdict (NO LLM CALL)"
""")
