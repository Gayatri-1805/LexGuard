# API Optimization: Eliminating Unnecessary LLM Calls

## Problem Identified

**Root Cause**: The API was exhausting API keys after only ~50 test cases because **EVERY request was calling the LLM for claim extraction**, even for simple single-sentence claims that were already atomic.

### API Call Analysis (Before Fix):
```
Test case → extract_claims() [🔴 LLM API call] → kb_lookup() [✅ No API] → verdict [✅ No API if in KB]
```

For 70 test cases:
- **70 LLM calls for claim extraction** (unnecessary!)
- **~15-20 LLM calls for web verification** (only for claims not in KB)
- **Total: ~90 API calls** 

### Expected Behavior:
For test cases with claims from IT Act KB:
```
Test case → extract_claims() [✅ No API] → kb_lookup() [✅ No API] → KB verdict [✅ No API]
```

For test cases with hallucinations:
```
Test case → extract_claims() [✅ No API] → kb_lookup() [✅ No API] → LLM web verification [🔴 LLM API call]
```

## Solution Implemented

### 1. Created Simple Claim Extractor (`simple_claim_extractor.py`)
- **No LLM calls** - uses rule-based text splitting
- Two functions:
  - `extract_claims_simple()` - splits by sentences
  - `extract_claims_single()` - treats entire input as one claim (best for test cases)
- Automatically detects claim type based on keywords
- Extracts section references using regex

### 2. Modified API Route (`api/routes/check.py`)
- Added environment variable `USE_SIMPLE_EXTRACTOR`
- When `USE_SIMPLE_EXTRACTOR=true`:
  - Uses rule-based extractor (NO API cost)
  - Perfect for test cases with atomic claims
- When `USE_SIMPLE_EXTRACTOR=false`:
  - Uses LLM-based extractor (API cost)
  - Needed for complex multi-claim paragraphs

### 3. Updated Environment Configuration (`.env`)
```bash
# Set to "true" for testing with atomic claims (NO API cost)
# Set to "false" for production with complex paragraphs (API cost)
USE_SIMPLE_EXTRACTOR=true
```

## Results (Expected After Fix)

### API Call Reduction:
- **Before**: 70 claims × 1 extraction call = **70 LLM calls**
- **After**: 70 claims × 0 extraction calls = **0 LLM calls** for extraction

### For Your 70 Test Cases:
- **35 SAFE cases** (in KB) → 0 API calls ✅
- **20 ABSTAIN cases** (partial in KB) → 0-20 API calls (depends on KB hits)
- **15 FLAGGED cases** (not in KB) → 15 API calls for web verification

**Total API calls: ~15-35** instead of ~90 (60-75% reduction!)

## KB Lookup Verification

Diagnostic tests confirmed:
```
✅ Section 66 → exact match (score: 0.95) → KB verdict (NO LLM)
✅ Section 66A → exact match (score: 0.95) → KB verdict (NO LLM)
✅ Section 43A → exact match (score: 0.95) → KB verdict (NO LLM)
✅ General IT Act claims → semantic match → KB verdict (NO LLM)
```

## How to Use

### For Testing (Atomic Claims):
```bash
# In .env file
USE_SIMPLE_EXTRACTOR=true

# Run tests
python run_70_tests.py
```

### For Production (Complex Text):
```bash
# In .env file  
USE_SIMPLE_EXTRACTOR=false

# Start server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## Key Findings

1. ✅ **KB has 115 sections** loaded properly
2. ✅ **Exact section lookup working** (PostgreSQL)
3. ✅ **Semantic search working** (FAISS)
4. ✅ **KB verdict generation working** (no LLM needed)
5. ❌ **Claim extraction was the bottleneck** (fixed with simple extractor)

## Recommendations

1. **For Testing**: Always use `USE_SIMPLE_EXTRACTOR=true`
2. **For Production**: 
   - Use simple extractor for simple inputs (single claims, Q&A)
   - Use LLM extractor for complex inputs (multi-paragraph legal text)
3. **Monitor API Usage**: Track which stage uses API calls
4. **Consider Caching**: Cache claim extraction results for repeated texts

## Files Modified

- ✅ `detection-engine/stages/simple_claim_extractor.py` (new)
- ✅ `api-and-sdk/api/routes/check.py` (modified)
- ✅ `api-and-sdk/.env` (added USE_SIMPLE_EXTRACTOR)
- ✅ `api-and-sdk/test_cases_70_it_act.json` (updated labels to SAFE/ABSTAIN/FLAGGED)
- ✅ `api-and-sdk/run_70_tests.py` (fixed label mapping)

## Next Steps

1. Restart the API server with `USE_SIMPLE_EXTRACTOR=true`
2. Re-run the 70 test cases
3. Verify API usage is minimal (only for non-KB claims)
4. Check that accuracy improves with proper flow
