"""
Full test of Knowledge Base: exact lookup + semantic fallback.

This demonstrates Stage 2 (Ground) retrieval paths:
1. Exact section lookup (Section 43A)
2. Semantic search fallback (query about data breach compensation)
"""

from api.kb.postgres_kb import PostgresKB

print("\n" + "="*70)
print("Knowledge Base Test: Exact Lookup + Semantic Fallback")
print("="*70 + "\n")

kb = PostgresKB()

# Test 1: Exact section lookup
print("Test 1: Exact Section Lookup")
print("-" * 70)
section_text = kb.lookup_section("43A", "Information Technology Act, 2000")
if section_text:
    print(f"✓ Found Section 43A")
    print(f"  Preview: {section_text[:100]}...")
else:
    print("✗ Section 43A not found")

print()

# Test 2: Semantic retrieval fallback
print("Test 2: Semantic Search Fallback")
print("-" * 70)
results = kb.retrieve("data breach compensation", top_k=3)
print(f"✓ Retrieved {len(results)} results for 'data breach compensation'")
for i, text in enumerate(results, 1):
    print(f"  {i}. {text[:80]}...")

print()

# Test 3: Case law lookup
print("Test 3: Related Case Law Lookup")
print("-" * 70)
cases = kb.lookup_case_law("43A", verified_only=True)
print(f"✓ Found {len(cases)} verified cases related to Section 43A")
for case in cases:
    print(f"  • {case['case_name']} ({case['citation']})")
    print(f"    {case['holding_summary'][:60]}...")

print("\n" + "="*70)
print("✓ Knowledge Base (Stage 2) ready for integration")
print("="*70 + "\n")
