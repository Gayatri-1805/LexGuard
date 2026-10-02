# Accuracy Improvement Plan: From 57% to 91-95%

## Current State Analysis

**Overall Accuracy: 57.1%**
- SAFE cases: 71.4% (25/35 correct)
- ABSTAIN cases: 50.0% (10/20 correct)  
- FLAGGED cases: 33.3% (5/15 correct)

**Target: 91-95% overall accuracy**

## Root Causes Identified

### 1. Missing Sections in KB (Critical) 🔴
From server logs:
```
kb_lookup | exact_match=FAILED | section=70A | no_content
kb_lookup | exact_match=FAILED | section=3A | no_content
kb_lookup | exact_match=FAILED | section=72A | no_content
kb_lookup | exact_match=FAILED | section=84A | no_content
```

**Impact**: Cases 19, 26, 42, 47 failing because sections exist in IT Act but not in DB

**Solution**: Load missing sections into PostgreSQL KB

### 2. LLM Web Verifier JSON Parsing Failures (High Priority) 🟡
```
llm_web_verifier | JSON parse failed on attempt 2
Error: Unterminated string starting at: line 5 column 25
```

**Impact**: Hallucinations not properly verified, causing false ABSTAIN results

**Solution**: Fix JSON response handling in llm_web_verifier.py

### 3. Weak Hallucination Detection (High Priority) 🟡
- Only 5/15 FLAGGED cases detected correctly (33.3%)
- 10 hallucinations misclassified as SAFE or ABSTAIN

**Impact**: Major source of false negatives

**Solution**: Improve non-existent section detection logic

### 4. ABSTAIN Classification Too Aggressive (Medium) 🟢
- 27 cases marked ABSTAIN (should be ~10-15)
- Low confidence threshold causing over-abstaining

**Impact**: Reduces both precision and recall

**Solution**: Adjust trust index thresholds and decision logic

## Improvement Steps (Prioritized)

### Step 1: Fix Missing KB Sections ⭐ HIGHEST IMPACT
**Expected Improvement: +10-15% accuracy**

Missing sections that need to be added:
- Section 3A (Electronic signature)
- Section 70A (National nodal agency)  
- Section 72A (Disclosure in breach of contract)
- Section 84A (Encryption modes)

Action: Check if these exist in source PDF but weren't parsed

### Step 2: Fix LLM Web Verifier JSON Parsing ⭐ HIGH IMPACT
**Expected Improvement: +8-12% accuracy**

Current issues:
- Unterminated strings in JSON responses
- LLM returning truncated JSON
- No fallback when parsing fails

Actions:
1. Add better JSON extraction (look for {...} blocks)
2. Increase max_tokens for LLM response
3. Add retry with explicit JSON formatting instructions

### Step 3: Improve Non-Existent Section Detection ⭐ HIGH IMPACT  
**Expected Improvement: +10-15% accuracy**

Current: Only detects if section lookup fails
Problem: Semantic search might find "related" sections

Solution:
1. After KB miss, check if section number exists in section list
2. If claim references Section XYZ but XYZ not in KB → likely hallucination
3. Use section number validation before calling web verifier

### Step 4: Optimize Decision Thresholds 🔧 MEDIUM IMPACT
**Expected Improvement: +5-8% accuracy**

Current thresholds may be too conservative:
```python
# Current (estimated from behavior)
SAFE threshold: trust_index >= 0.75
ABSTAIN range: 0.25 < trust_index < 0.75
FLAGGED threshold: trust_index <= 0.25
```

Proposed:
```python
SAFE threshold: trust_index >= 0.70  (lower = more SAFE decisions)
ABSTAIN range: 0.40 < trust_index < 0.70  (narrower band)
FLAGGED threshold: trust_index <= 0.40  (catch more hallucinations)
```

### Step 5: Enhance Contradiction Detection 🔧 LOW-MEDIUM IMPACT
**Expected Improvement: +3-5% accuracy**

Current: Simple negation detection
Problem: Misses complex contradictions

Actions:
1. Improve _detect_contradiction() heuristics
2. Add numeric mismatch detection (e.g., "3 years" vs "5 years")
3. Add section number mismatch detection

## Implementation Priority

### Phase 1: Quick Wins (1-2 hours) 🎯
1. ✅ Add missing KB sections (Step 1)
2. ✅ Fix section validation logic (Step 3)
3. ✅ Adjust decision thresholds (Step 4)

**Expected Result: 75-80% accuracy**

### Phase 2: Core Fixes (2-3 hours)
1. Fix LLM JSON parsing (Step 2)
2. Enhance contradiction detection (Step 5)

**Expected Result: 85-90% accuracy**

### Phase 3: Fine-Tuning (1-2 hours)
1. Optimize threshold values based on test results
2. Add edge case handling
3. Improve logging for debugging

**Expected Result: 91-95% accuracy** ✅

## Testing Strategy

After each phase:
1. Run full 70-case test suite
2. Analyze confusion matrix (SAFE/ABSTAIN/FLAGGED)
3. Identify remaining failure patterns
4. Adjust and repeat

## Success Metrics

Target breakdown for 91-95% accuracy:
- SAFE cases: 90-95% accuracy (32-33/35 correct)
- ABSTAIN cases: 85-90% accuracy (17-18/20 correct)
- FLAGGED cases: 90-95% accuracy (13-14/15 correct)

## Next Actions

1. Check source PDF for missing sections
2. Update PostgreSQL ingestion script
3. Implement section validation logic
4. Fix JSON parsing
5. Re-run tests and measure improvement
