#!/usr/bin/env python
"""
Analyze 250-case test results to find where rate limit kicked in
"""
import json

# Load the final results
with open('test_results_250_final_20260911_163209.json', 'r') as f:
    data = json.load(f)

results = data['individual_results']

# Find where rate limiting started affecting results
# Rate limit causes ABSTAIN with trust_index = 0.5
# Before rate limit, we should see varied trust indices and different decisions

non_abstain = [r for r in results if r['actual_decision'] != 'ABSTAIN']
abstain_with_default = [r for r in results if r['actual_decision'] == 'ABSTAIN' and r['trust_index'] == 0.5]
abstain_with_real = [r for r in results if r['actual_decision'] == 'ABSTAIN' and r['trust_index'] != 0.5]
errors = [r for r in results if r['status'] == 'error']

print('='*70)
print('250-CASE TEST RESULTS ANALYSIS')
print('='*70)
print(f'Total test cases: {len(results)}')
print(f'Non-ABSTAIN decisions: {len(non_abstain)}')
print(f'ABSTAIN with default trust (0.5): {len(abstain_with_default)}')
print(f'ABSTAIN with varied trust: {len(abstain_with_real)}')
print(f'ERROR status: {len(errors)}')
print()

# Analyze first 50 (should be before major rate limit)
print('FIRST 50 CASES (Before Rate Limit Impact):')
print('-'*70)
first_50 = results[:50]
correct_50 = sum(1 for r in first_50 if r['decision_correct'])
print(f'Correct decisions: {correct_50}/50 ({correct_50/50*100:.1f}%)')
print()

# Show decision distribution in first 50
from collections import Counter
decisions_50 = Counter(r['actual_decision'] for r in first_50)
print('Decision breakdown (first 50):')
for decision, count in decisions_50.items():
    print(f'  {decision}: {count} ({count/50*100:.1f}%)')
print()

# Check accuracy by category in first 50
categories = {}
for r in first_50:
    cat = r['expected_category']
    if cat not in categories:
        categories[cat] = {'total': 0, 'correct': 0}
    categories[cat]['total'] += 1
    if r['decision_correct']:
        categories[cat]['correct'] += 1

print('Accuracy by category (first 50):')
for cat, stats in categories.items():
    acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
    print(f'  {cat:25s}: {stats["correct"]}/{stats["total"]} ({acc:.1f}%)')
print()

# Find first cases with different decisions
print('Sample results showing decision variety:')
print('-'*70)
shown = {'FLAGGED': 0, 'ABSTAIN': 0, 'SAFE': 0, 'ERROR': 0}
for r in results:
    decision = r['actual_decision']
    if shown[decision] < 3:  # Show first 3 of each type
        status = 'CORRECT' if r['decision_correct'] else 'WRONG'
        print(f'{decision:8s} ({status}): {r["id"]:30s} Expected:{r["expected_decision"]:8s} Trust:{r["trust_index"]:.3f}')
        shown[decision] += 1
    if all(v >= 3 for v in shown.values()):
        break
print()

# Check where errors started
if errors:
    first_error_idx = next(i for i, r in enumerate(results) if r['status'] == 'error')
    print(f'First ERROR appeared at case #{first_error_idx + 1}: {results[first_error_idx]["id"]}')
    print(f'Successful cases before errors: {first_error_idx}')
else:
    print('No ERROR status found')
