# Trust Score Calculation Methodology

## 📊 **Overview**

The **Trust Score** (also called Trust Index) is a **confidence metric** (0.0 to 1.0) that indicates how confident the system is about the accuracy of the analyzed text, based on verification against the legal knowledge base.

---

## 🧮 **Core Formula**

### **Step 1: Individual Verdict Labels → Numeric Scores**

Each claim extracted from the input text receives a verdict label after KB verification. These labels are mapped to numeric scores:

```python
LABEL_SCORES = {
    'SUPPORTED':           1.0,    # ✅ Strong evidence supports claim
    'ENTAILED':            1.0,    # ✅ KB logically entails claim
    'PARTIALLY_SUPPORTED': 0.5,    # ⚠️  Partial evidence found
    'CONTRADICTED':        0.0,    # ❌ KB contradicts claim
    'UNVERIFIABLE':        0.5,    # ❓ Insufficient evidence
    'NOT_ENOUGH_INFO':     0.5,    # ❓ Cannot determine
    'LOW_RISK_SKIP':       None    # 🔇 Excluded from calculation
}
```

### **Step 2: Aggregate Trust Score**

```
Trust Score = (Sum of all verdict scores) / (Number of verdicts)
```

**Example 1: Perfect Trust**
- 3 claims, all `SUPPORTED` (1.0, 1.0, 1.0)
- Trust = (1.0 + 1.0 + 1.0) / 3 = **1.000** ✅

**Example 2: Complete Hallucination**
- 2 claims, both `CONTRADICTED` (0.0, 0.0)
- Trust = (0.0 + 0.0) / 2 = **0.000** ❌

**Example 3: Mixed Evidence**
- 3 claims: `SUPPORTED` (1.0), `PARTIALLY_SUPPORTED` (0.5), `CONTRADICTED` (0.0)
- Trust = (1.0 + 0.5 + 0.0) / 3 = **0.500** ⚠️

---

## 🎯 **Trust Score Interpretation**

| **Score Range** | **Meaning** | **Typical Scenario** |
|-----------------|-------------|---------------------|
| **0.90 - 1.00** | Very High Trust | All claims strongly supported by KB |
| **0.75 - 0.89** | High Trust | Most claims supported, minor uncertainties |
| **0.50 - 0.74** | Medium Trust | Mixed evidence, some contradictions |
| **0.25 - 0.49** | Low Trust | Significant contradictions present |
| **0.00 - 0.24** | Very Low Trust | Most/all claims contradicted by KB |

---

## 🚦 **Decision Logic (Trust → SAFE/ABSTAIN/FLAGGED)**

The system uses **pattern analysis** in addition to trust score to make final decisions:

### **Key Metrics Calculated:**

```python
contradiction_ratio = count(CONTRADICTED) / total_verdicts
support_ratio = count(SUPPORTED + ENTAILED) / total_verdicts
```

### **Decision Rules (Priority Order):**

```python
# 1. HIGH CONTRADICTION (40%+) → FLAGGED
if contradiction_ratio >= 0.4:
    decision = FLAGGED
    
# 2. ONLY CONTRADICTIONS, NO SUPPORT → FLAGGED  
elif has_contradicted and not has_supported:
    decision = FLAGGED

# 3. MIXED EVIDENCE WITH SIGNIFICANT CONTRADICTIONS (20%+) → ABSTAIN
elif has_contradicted and has_supported and contradiction_ratio >= 0.2:
    decision = ABSTAIN

# 4. STRONG SUPPORT WITHOUT CONTRADICTIONS (60%+) → SAFE
elif support_ratio >= 0.6 and not has_contradicted:
    decision = SAFE

# 5. HIGH TRUST WITH SUPPORT, NO CONTRADICTIONS → SAFE
elif has_supported and trust >= 0.75 and not has_contradicted:
    decision = SAFE

# 6. PARTIAL SUPPORT WITHOUT CONTRADICTIONS → ABSTAIN
elif has_partial and not has_contradicted:
    decision = ABSTAIN

# 7. ANY MIXED EVIDENCE → ABSTAIN
elif has_contradicted and has_supported:
    decision = ABSTAIN

# 8. VERY HIGH TRUST (80%+) → SAFE
elif trust >= 0.8:
    decision = SAFE

# 9. VERY LOW TRUST (≤30%) → FLAGGED
elif trust <= 0.3:
    decision = FLAGGED

# 10. UNCERTAIN MIDDLE GROUND → ABSTAIN
else:
    decision = ABSTAIN
```

---

## 📊 **Real-World Examples**

### **Example 1: Accurate Statement ✅**

**Input Text:**
```
"Section 10A of the IT Act validates electronic contracts."
```

**Pipeline Results:**
1. **Claims Extracted**: 1
   - "Section 10A validates electronic contracts"
   
2. **KB Lookup**: 
   - Exact match found: Section 10A text retrieved
   - Score: 0.95 (exact match)
   
3. **Verdict**: `SUPPORTED` (1.0)
   - Evidence: Full Section 10A text
   - Reasoning: "Claim accurately describes Section 10A provisions"

4. **Trust Calculation**:
   - Scores: [1.0]
   - Trust = 1.0 / 1 = **1.000**
   
5. **Decision Logic**:
   - support_ratio = 1.0 (100%)
   - contradiction_ratio = 0.0 (0%)
   - Rule #4 applies: "Strong support without contradictions"
   - **Decision: SAFE** ✅

---

### **Example 2: Complete Hallucination ❌**

**Input Text:**
```
"Section 43 of the IT Act prescribes mandatory imprisonment of 5-10 years for data breaches."
```

**Pipeline Results:**
1. **Claims Extracted**: 2
   - "Section 43 prescribes mandatory imprisonment"
   - "Punishment is 5-10 years for data breaches"
   
2. **KB Lookup**: 
   - Exact match: Section 43 text retrieved
   - Score: 0.95 (exact match)
   
3. **Verdicts**:
   - Claim 1: `CONTRADICTED` (0.0)
     - Evidence: "Section 43 provides only civil liability, no criminal penalties"
   - Claim 2: `CONTRADICTED` (0.0)
     - Evidence: "No imprisonment provision exists in Section 43"

4. **Trust Calculation**:
   - Scores: [0.0, 0.0]
   - Trust = (0.0 + 0.0) / 2 = **0.000**
   
5. **Decision Logic**:
   - support_ratio = 0.0 (0%)
   - contradiction_ratio = 1.0 (100%)
   - Rule #1 applies: "High contradiction (≥40%)"
   - **Decision: FLAGGED** ❌

---

### **Example 3: Partial Hallucination ⚠️**

**Input Text:**
```
"Section 67 of the IT Act punishes obscene material with three years imprisonment and fine up to ten lakh rupees."
```

**Pipeline Results:**
1. **Claims Extracted**: 3
   - "Section 67 punishes obscene material"
   - "Punishment includes three years imprisonment"
   - "Fine up to ten lakh rupees"
   
2. **KB Lookup**: 
   - Exact match: Section 67 text retrieved
   - Score: 0.95
   
3. **Verdicts**:
   - Claim 1: `SUPPORTED` (1.0)
     - Evidence: "Section 67 deals with obscene material in electronic form"
   - Claim 2: `SUPPORTED` (1.0)
     - Evidence: "Punishment may extend to three years imprisonment"
   - Claim 3: `CONTRADICTED` (0.0)
     - Evidence: "Fine is up to five lakh rupees, not ten lakh"

4. **Trust Calculation**:
   - Scores: [1.0, 1.0, 0.0]
   - Trust = (1.0 + 1.0 + 0.0) / 3 = **0.667**
   
5. **Decision Logic**:
   - support_ratio = 0.67 (67%)
   - contradiction_ratio = 0.33 (33%)
   - has_contradicted = True
   - has_supported = True
   - Rule #3 applies: "Mixed evidence with significant contradictions"
   - **Decision: ABSTAIN** ⚠️

---

### **Example 4: Unverifiable Statement ❓**

**Input Text:**
```
"The IT Act may impose penalties under multiple sections for a single cyber crime."
```

**Pipeline Results:**
1. **Claims Extracted**: 1
   - "IT Act may impose penalties under multiple sections"
   
2. **KB Lookup**: 
   - Semantic search: Found general IT Act overview
   - Score: 0.42 (below threshold 0.45)
   - KB Hit: False
   
3. **Verdict**: `UNVERIFIABLE` (0.5)
   - Evidence: None
   - Reasoning: "Vague claim, insufficient specific evidence to verify"

4. **Trust Calculation**:
   - Scores: [0.5]
   - Trust = 0.5 / 1 = **0.500**
   
5. **Decision Logic**:
   - No contradictions, no strong support
   - Trust = 0.5 (middle ground)
   - Rule #10 applies: "Uncertain middle ground"
   - **Decision: ABSTAIN** ⚠️

---

## 🔬 **Advanced Metrics**

### **Contradiction Ratio**
```
contradiction_ratio = count(CONTRADICTED verdicts) / total_verdicts
```

**Purpose**: Measure how much of the text is actively contradicted by KB

**Thresholds**:
- ≥40% → Automatic FLAGGED
- ≥20% (with mixed evidence) → ABSTAIN
- <20% → Consider other factors

---

### **Support Ratio**
```
support_ratio = count(SUPPORTED + ENTAILED verdicts) / total_verdicts
```

**Purpose**: Measure how much of the text is strongly supported by KB

**Thresholds**:
- ≥60% (without contradictions) → SAFE
- <60% → Consider other factors

---

### **Verdict Patterns**

The system analyzes **combinations** of verdict types:

| **Pattern** | **Trust** | **Decision** | **Interpretation** |
|-------------|-----------|--------------|-------------------|
| All SUPPORTED | 1.00 | SAFE | Perfect accuracy ✅ |
| All CONTRADICTED | 0.00 | FLAGGED | Complete hallucination ❌ |
| All UNVERIFIABLE | 0.50 | ABSTAIN | Cannot verify ❓ |
| Mix: SUPPORTED + CONTRADICTED | 0.33-0.67 | ABSTAIN | Partial hallucination ⚠️ |
| Mix: SUPPORTED + PARTIAL | 0.67-0.83 | SAFE/ABSTAIN | Mostly accurate ✅ |
| Mix: CONTRADICTED + PARTIAL | 0.17-0.33 | FLAGGED/ABSTAIN | Mostly false ❌ |

---

## 📐 **Mathematical Properties**

### **1. Bounded Range**
```
0.0 ≤ Trust Score ≤ 1.0
```
Always normalized to [0, 1] range

### **2. Linear Averaging**
```
Trust = Σ(scores) / n
```
Simple arithmetic mean for interpretability

### **3. Symmetric Treatment**
- SUPPORTED (1.0) and CONTRADICTED (0.0) are equidistant from neutral (0.5)
- Allows balanced detection of both false positives and false negatives

### **4. Excluded Labels**
- `LOW_RISK_SKIP` (score = None) is excluded from calculation
- Only labels with evidence contribute to trust score

---

## 🎯 **Design Rationale**

### **Why Simple Averaging?**

**✅ Advantages:**
1. **Interpretable**: Easy to understand and explain
2. **Transparent**: Clear mapping from verdicts to scores
3. **Calibrated**: 0.5 represents true uncertainty
4. **Robust**: Resistant to outliers with multiple claims

**❌ Alternatives Considered but Rejected:**
- **Minimum score**: Too pessimistic, one contradiction flags everything
- **Maximum score**: Too optimistic, ignores contradictions
- **Weighted average**: Requires tuning, less transparent

---

### **Why Pattern Analysis?**

Pure trust score thresholds (e.g., "SAFE if trust > 0.8") are insufficient because:

1. **Context matters**: 
   - Trust = 0.6 from [SUPPORTED, UNVERIFIABLE, UNVERIFIABLE] → Likely SAFE
   - Trust = 0.6 from [SUPPORTED, SUPPORTED, CONTRADICTED] → Should ABSTAIN

2. **Edge cases need special handling**:
   - All UNVERIFIABLE → ABSTAIN (not SAFE despite trust = 0.5)
   - 1 CONTRADICTED + 9 SUPPORTED → Maybe ABSTAIN (partial hallucination)

3. **Legal domain requires conservatism**:
   - Any contradiction is serious
   - Prefer ABSTAIN over false SAFE

---

## 🔧 **Tuning Parameters**

### **Current Thresholds:**

```python
CONTRADICTION_THRESHOLD = 0.4   # 40%+ contradictions → FLAGGED
SIGNIFICANT_CONTRADICTION = 0.2  # 20%+ → ABSTAIN (with mixed evidence)
STRONG_SUPPORT = 0.6            # 60%+ support → SAFE (no contradictions)
HIGH_TRUST = 0.75               # Required for SAFE (with some support)
VERY_HIGH_TRUST = 0.8           # Automatic SAFE
VERY_LOW_TRUST = 0.3            # Automatic FLAGGED
```

### **Tuning Guidelines:**

**To be MORE STRICT (reduce false negatives):**
- Lower `CONTRADICTION_THRESHOLD` (e.g., 0.3)
- Raise `STRONG_SUPPORT` (e.g., 0.7)
- Raise `HIGH_TRUST` (e.g., 0.8)

**To be MORE LENIENT (reduce false positives):**
- Raise `CONTRADICTION_THRESHOLD` (e.g., 0.5)
- Lower `STRONG_SUPPORT` (e.g., 0.5)
- Lower `HIGH_TRUST` (e.g., 0.7)

---

## 📊 **Validation & Calibration**

### **Expected Trust Score Distributions:**

| **Text Type** | **Expected Trust** | **Expected Decision** |
|---------------|-------------------|-----------------------|
| Fully Accurate Legal Text | 0.85 - 1.00 | SAFE |
| Mostly Accurate (minor errors) | 0.60 - 0.80 | SAFE / ABSTAIN |
| Partial Hallucination | 0.40 - 0.70 | ABSTAIN |
| Significant Hallucination | 0.15 - 0.45 | FLAGGED / ABSTAIN |
| Complete Hallucination | 0.00 - 0.20 | FLAGGED |
| Unverifiable Text | 0.45 - 0.55 | ABSTAIN |

### **Calibration Metrics:**

**Good calibration means:**
- Trust = 1.0 → 100% of cases are actually accurate
- Trust = 0.5 → 50% accurate, 50% inaccurate
- Trust = 0.0 → 0% accurate (100% hallucinated)

**To verify calibration:**
1. Bin predictions by trust score (0-0.1, 0.1-0.2, ..., 0.9-1.0)
2. Calculate actual accuracy in each bin
3. Plot: Expected (trust) vs Actual (accuracy)
4. Perfect calibration = diagonal line

---

## 🎓 **Summary**

### **Key Points:**

1. **Trust Score = Average of verdict scores** (0.0 to 1.0)
2. **Verdict labels map to scores**: SUPPORTED=1.0, CONTRADICTED=0.0, etc.
3. **Decision uses pattern analysis**: Not just thresholds, but verdict combinations
4. **Conservative approach**: Prefer ABSTAIN over wrong SAFE/FLAGGED
5. **Tunable parameters**: Can adjust thresholds based on use case

### **Strengths:**

✅ Transparent and interpretable  
✅ Handles multi-claim texts well  
✅ Balanced false positive/negative tradeoff  
✅ Domain-appropriate conservatism  

### **Limitations:**

⚠️ Equal weight to all claims (no claim importance weighting)  
⚠️ Requires good KB coverage for accurate scoring  
⚠️ Threshold-based decisions need domain tuning  

---

**For questions or suggestions, refer to the implementation in:**  
`api-and-sdk/api/routes/check.py` (function `_compute_trust`)
