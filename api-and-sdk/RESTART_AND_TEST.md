# Restart API and Run Tests

## What We Fixed:

1. ✅ **Added section validation logic** - Catches hallucinated sections (66G, 68A, 71A, etc.)
2. ✅ **Added missing sections** - 70A, 72A, 84A now in PostgreSQL KB
3. ✅ **Rebuilt FAISS index** - 126 vectors (was 123)
4. ✅ **Optimized claim extraction** - No LLM calls for simple claims (USE_SIMPLE_EXTRACTOR=true)

## Expected Accuracy Improvement:

**Before**: 57.1% overall
- SAFE: 71.4% (25/35)
- ABSTAIN: 50.0% (10/20)
- FLAGGED: 33.3% (5/15)

**After Phase 1**: 75-80% overall (estimated)
- SAFE: 85-90% (30-32/35) - missing sections now available
- ABSTAIN: 70-75% (14-15/20) - better validation
- FLAGGED: 70-80% (10-12/15) - section validation catches hallucinations

## Commands to Run:

### 1. Restart API Server
```cmd
cd D:\projects\HALO\legal-hallucination-detector\api-and-sdk
set PYTHONPATH=D:\projects\HALO\legal-hallucination-detector;D:\projects\HALO\legal-hallucination-detector\api-and-sdk
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Note**: Stop the current server first (Ctrl+C), then restart it to load:
- New section validation logic
- Updated FAISS index with 126 vectors
- Simple claim extractor

### 2. Run Tests (in a new terminal)
```cmd
cd D:\projects\HALO\legal-hallucination-detector\api-and-sdk
python run_70_tests.py
```

## What to Look For:

### In Server Logs:
```
✓ Loaded index with 126 vectors  (was 123 before)
check._route_claim | section=66G not in KB | treating as hallucination
```

### In Test Results:
- **Hallucinated sections** (66G, 68A, 71A, 44A, 75A, 82A, 66H) → Should show **FLAGGED**
- **Real sections** (70A, 72A, 84A) → Should show **SAFE** or **ABSTAIN** (not errors)
- **Overall accuracy** → Should be **75-80%** or higher

## If Accuracy Is Still Below 75%:

Run diagnostic to see remaining issues:
```cmd
python -c "import json; data = json.load(open('test_results_70_it_act_LATEST.json')); wrong = [r for r in data['individual_results'] if not r['decision_correct']]; print(f'Failed cases: {len(wrong)}'); [print(f\"Case {r['id']}: Expected {r['expected_decision']}, Got {r['actual_decision']}\") for r in wrong[:10]]"
```

This will show which specific cases are still failing so we can target Phase 2 fixes.
