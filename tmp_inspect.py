import json
from pathlib import Path
from collections import Counter

gold_path = 'dashboard-and-eval/eval/gold_set/gold_set.jsonl'
items = [json.loads(l) for l in Path(gold_path).read_text(encoding='utf-8').strip().splitlines() if l.strip()]
print(f'Total items: {len(items)}')

labels = Counter(item['ground_truth'] for item in items)
types  = Counter(item.get('claim_type','?') for item in items)
print('Label distribution:', dict(labels))
print('Type distribution: ', dict(types))
print()
print('Sample items:')
for item in items[:3]:
    print(f"  [{item['ground_truth']}] {item['text'][:100]}")
