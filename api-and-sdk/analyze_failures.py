"""Analyze test failures to identify patterns."""
import json

# Load results
with open('test_results_70_it_act_20260913_000158.json') as f:
    data = json.load(f)

# Load test cases for claim text
with open('test_cases_70_it_act.json') as f:
    test_data = json.load(f)
    test_cases = {tc['id']: tc for tc in test_data['test_cases']}

wrong = [r for r in data['individual_results'] if not r['decision_correct']]

print("=" * 80)
print(f"FAILURE ANALYSIS - {len(wrong)}/70 cases failed")
print("=" * 80)

# Group by failure type
false_positives = [r for r in wrong if r['expected_decision'] == 'SAFE' and r['actual_decision'] == 'FLAGGED']
false_negatives = [r for r in wrong if r['expected_decision'] == 'FLAGGED' and r['actual_decision'] != 'FLAGGED']
abstain_issues = [r for r in wrong if 'ABSTAIN' in [r['expected_decision'], r['actual_decision']]]

print(f"\n📊 Failure Types:")
print(f"   False Positives (SAFE→FLAGGED): {len(false_positives)}")
print(f"   False Negatives (FLAGGED→SAFE/ABSTAIN): {len(false_negatives)}")
print(f"   ABSTAIN misclassifications: {len(abstain_issues)}")

print(f"\n❌ FALSE POSITIVES (Correct claims marked as hallucinations):")
print("─" * 80)
for r in false_positives[:5]:
    tc = test_cases.get(r['id'], {})
    print(f"Case {r['id']}: {tc.get('claim', 'N/A')[:70]}")
    print(f"   Section: {tc.get('section_reference', 'N/A')}")
    print(f"   Expected: SAFE, Got: FLAGGED")
    print()

print(f"\n❌ FALSE NEGATIVES (Hallucinations not detected):")
print("─" * 80)
for r in false_negatives[:5]:
    tc = test_cases.get(r['id'], {})
    print(f"Case {r['id']}: {tc.get('claim', 'N/A')[:70]}")
    print(f"   Reason: {tc.get('reason', 'N/A')}")
    print(f"   Expected: FLAGGED, Got: {r['actual_decision']}")
    print()

print(f"\n⚠️  ABSTAIN ISSUES:")
print("─" * 80)
for r in abstain_issues[:8]:
    tc = test_cases.get(r['id'], {})
    print(f"Case {r['id']}: Expected {r['expected_decision']}, Got {r['actual_decision']}")
    print(f"   Claim: {tc.get('claim', 'N/A')[:70]}")
    print()

print("\n" + "=" * 80)
print("KEY INSIGHTS")
print("=" * 80)
print("""
To reach 91-95% accuracy, we need to:
1. Fix false positives - some legitimate sections being marked as hallucinations
2. Improve ABSTAIN detection - partial hallucinations not being caught
3. Strengthen hallucination detection - some fake sections slipping through
""")
