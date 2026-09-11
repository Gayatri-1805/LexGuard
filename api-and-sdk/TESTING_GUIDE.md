# Comprehensive Testing & Evaluation Guide

## 🎯 **Overview**

This guide explains how to run comprehensive tests and generate visualizations for the Legal Hallucination Detection System.

---

## 📁 **Test Suite Components**

### **1. Test Cases** (`comprehensive_test_cases.py`)
- **25 test cases** covering diverse scenarios
- **4 categories**: Complete hallucinations, Partial hallucinations, Accurate statements, Edge cases
- **3 difficulty levels**: Easy, Medium, Hard

### **2. Test Runner** (`run_comprehensive_tests.py`)
- Automated test execution
- Detailed metrics calculation
- JSON/CSV export for analysis

### **3. Visualization Tool** (`visualize_results.py`)
- Accuracy charts (overall, by category, by difficulty)
- Confusion matrix heatmap
- Performance metrics (latency, KB hits)
- Detailed analysis graphs

---

## 🚀 **Quick Start**

### **Step 1: View Test Statistics**

```bash
python comprehensive_test_cases.py
```

**Output**:
```
======================================================================
COMPREHENSIVE TEST SUITE STATISTICS
======================================================================

Total Test Cases: 25

📊 By Category:
  accurate                 :  6 ( 24.0%)
  edge_case                :  5 ( 20.0%)
  hallucinated             :  5 ( 20.0%)
  partially_hallucinated   :  5 ( 20.0%)

🎯 By Difficulty:
  easy                     :  8 ( 32.0%)
  hard                     :  9 ( 36.0%)
  medium                   :  8 ( 32.0%)

✅ By Expected Decision:
  ABSTAIN                  :  6 ( 24.0%)
  FLAGGED                  :  6 ( 24.0%)
  SAFE                     : 10 ( 40.0%)
```

---

### **Step 2: Run Comprehensive Tests**

**Ensure API server is running:**
```bash
# In terminal 1:
python run_api.py
```

**Run tests:**
```bash
# In terminal 2:
python run_comprehensive_tests.py
```

**What happens**:
1. Connects to API server
2. Runs all 25 test cases
3. Calculates comprehensive metrics
4. Exports results to JSON and CSV
5. Prints detailed analysis

**Sample Output**:
```
🧪 STARTING COMPREHENSIVE TEST SUITE
======================================================================

Test Suite Overview:
   Total Cases: 25
   Categories: accurate, edge_case, hallucinated, partially_hallucinated
   Difficulties: easy, medium, hard

✅ API Server: Accessible

🏃 Running 25 test cases...
   This may take several minutes...

   [ 1/25] Testing hallucination_001... ✅ FLAGGED (expected FLAGGED) - 41.2s
   [ 2/25] Testing hallucination_002... ✅ FLAGGED (expected FLAGGED) - 17.9s
   ...
```

---

### **Step 3: Generate Visualizations**

**Install required packages** (if not already installed):
```bash
pip install matplotlib seaborn pandas
```

**Generate visualizations:**
```bash
python visualize_results.py
```

**Or specify a specific results file:**
```bash
python visualize_results.py comprehensive_test_20260911_143052.json
```

**Generated files** (saved to `visualizations/` directory):
- `overall_accuracy.png` - Overall performance metrics
- `confusion_matrix.png` - Confusion matrix heatmap
- `performance_metrics.png` - Latency and KB hit analysis
- `detailed_analysis.png` - Detailed breakdown charts
- `summary_report.txt` - Text summary report

---

## 📊 **Understanding the Results**

### **Metrics Explained**

#### **1. Overall Accuracy**
```
Overall Accuracy: 72.0%
```
- Percentage of test cases where actual decision matched expected decision
- **Target**: ≥80% for production readiness

#### **2. Accuracy by Category**

```
✅ hallucinated              :  5/ 5 (100.0%)  ← Perfect detection!
⚠️ partially_hallucinated   :  3/ 5 ( 60.0%)  ← Needs improvement
✅ accurate                  :  5/ 6 ( 83.3%)  ← Good recognition
✅ edge_case                 :  4/ 5 ( 80.0%)  ← Handling edge cases well
```

**Interpretation**:
- ✅ Green (≥80%): Excellent performance
- ⚠️ Yellow (60-79%): Acceptable, room for improvement
- ❌ Red (<60%): Needs attention

#### **3. Accuracy by Difficulty**

```
✅ easy                      :  7/ 8 ( 87.5%)
✅ medium                    :  6/ 8 ( 75.0%)
⚠️ hard                      :  5/ 9 ( 55.6%)
```

**Interpretation**:
- System performs well on straightforward cases
- Struggles with complex/ambiguous scenarios

#### **4. Confusion Matrix**

```
FLAGGED → FLAGGED            :  5  ← Correct hallucination detection
SAFE → SAFE                  :  8  ← Correct accurate recognition
ABSTAIN → ABSTAIN            :  3  ← Correct abstention
FLAGGED → ABSTAIN            :  1  ← Missed hallucination
SAFE → ABSTAIN               :  2  ← Over-cautious
```

**Key patterns**:
- **Diagonal values**: Correct predictions (want these high)
- **Off-diagonal**: Misclassifications (want these low)

#### **5. Performance Metrics**

```
Avg Processing Time: 34.5s
KB Hit Rate: 52.3%
Total KB Hits: 47
Total Claims: 90
```

**Benchmarks**:
- Processing time <40s: Good
- KB hit rate >50%: Target met
- High KB hits = good evidence retrieval

---

## 🎨 **Understanding the Visualizations**

### **1. Overall Accuracy Chart**

**What it shows**:
- Pie chart: Correct vs incorrect predictions
- Bar charts: Accuracy by category and difficulty
- Summary metrics panel

**Look for**:
- Large green slice in pie chart (>80%)
- Most bars above 80% line
- Consistent performance across difficulties

---

### **2. Confusion Matrix Heatmap**

**What it shows**:
- Rows: Expected decisions
- Columns: Actual decisions
- Color intensity: Count of occurrences
- Green boxes: Correct predictions (diagonal)

**How to read**:
- Bright colors on diagonal = good
- Bright colors off-diagonal = problems
- Check which transitions are most common errors

---

### **3. Performance Metrics**

**Four subplots**:

1. **Processing Time Distribution**
   - Histogram of response times
   - Red line = average
   - Look for: Most cases <40s

2. **KB Hit Rate by Category**
   - Which categories get best KB coverage
   - Orange line = 50% target
   - Look for: All bars above target

3. **Trust Score Distribution**
   - Green: Correct predictions
   - Red: Incorrect predictions
   - Look for: Good separation between colors

4. **Claims vs KB Hits**
   - Scatter plot showing coverage
   - Diagonal = perfect KB hit rate
   - Green dots = correct, Red = incorrect
   - Look for: Green dots near diagonal

---

### **4. Detailed Analysis**

**Four subplots**:

1. **Accuracy vs Difficulty**
   - How accuracy changes with difficulty
   - Look for: Graceful degradation

2. **Success vs Errors**
   - Count of successful vs failed requests
   - Look for: Very few errors

3. **Processing Time by Category**
   - Which categories take longest
   - Look for: Consistent times

4. **Decision Distribution**
   - Pie chart of SAFE/ABSTAIN/FLAGGED
   - Look for: Balanced distribution

---

## 📈 **Grading Scale**

```
A+ (90-100%): Excellent - Production ready, exceeds expectations
A  (80-89%):  Very Good - Production ready, meets expectations
B  (70-79%):  Good - Usable with monitoring
C  (60-69%):  Fair - Needs improvement before production
D  (<60%):    Needs Work - Significant improvements required
```

---

## 🔧 **Troubleshooting**

### **Problem: API Connection Error**

```
❌ API Server: Not accessible at http://localhost:8000/api/check
```

**Solution**:
```bash
# Start the API server in separate terminal
python run_api.py
```

---

### **Problem: Import Errors for Visualization**

```
❌ Required packages not installed.
```

**Solution**:
```bash
pip install matplotlib seaborn pandas numpy
```

---

### **Problem: Tests Taking Too Long**

**Cause**: Some tests have 120s timeout

**Solution**: Run subset of tests by modifying `COMPREHENSIVE_TEST_CASES` in `comprehensive_test_cases.py`

---

### **Problem: Low Accuracy on Partial Hallucinations**

**Analysis**: Check confusion matrix for patterns:
- `ABSTAIN → SAFE`: System too confident
- `ABSTAIN → FLAGGED`: System too strict

**Solution**: Tune decision thresholds in `api/routes/check.py`

---

## 📊 **Sample Test Results Interpretation**

### **Example: Good Performance**

```
Overall Accuracy: 84.0% (21/25)

By Category:
  ✅ hallucinated: 5/5 (100%)  ← Perfect!
  ✅ accurate: 6/6 (100%)      ← Perfect!
  ✅ edge_case: 5/5 (100%)     ← Excellent!
  ⚠️ partially_hallucinated: 5/5 (60%) ← Only weak point

Grade: A (Very Good)
```

**Interpretation**:
- System excels at clear-cut cases
- Partial hallucinations are challenging (expected)
- Production-ready with monitoring on partial cases

---

### **Example: Needs Improvement**

```
Overall Accuracy: 56.0% (14/25)

By Category:
  ⚠️ hallucinated: 3/5 (60%)
  ❌ accurate: 3/6 (50%)
  ❌ edge_case: 2/5 (40%)
  ❌ partially_hallucinated: 1/5 (20%)

Grade: D (Needs Work)
```

**Interpretation**:
- Missing obvious hallucinations (check KB coverage)
- False positives on accurate statements (too strict)
- Not production-ready, needs tuning

**Action items**:
1. Check KB hit rates (likely low)
2. Review decision thresholds
3. Examine specific failed cases
4. Verify exact section matching working

---

## 🎯 **Success Criteria**

### **Minimum for Production**:
- ✅ Overall Accuracy: ≥80%
- ✅ Hallucination Detection: ≥90%
- ✅ Accurate Recognition: ≥85%
- ✅ KB Hit Rate: ≥50%
- ✅ Avg Processing Time: <40s
- ✅ Error Rate: <5%

### **Excellent Performance**:
- 🏆 Overall Accuracy: ≥90%
- 🏆 Hallucination Detection: 100%
- 🏆 Accurate Recognition: ≥95%
- 🏆 KB Hit Rate: ≥65%
- 🏆 Avg Processing Time: <30s
- 🏆 Error Rate: 0%

---

## 📚 **Files Generated**

### **Test Results**:
- `comprehensive_test_YYYYMMDD_HHMMSS.json` - Full results (JSON)
- `comprehensive_test_YYYYMMDD_HHMMSS.csv` - Results table (CSV)

### **Visualizations** (in `visualizations/` folder):
- `overall_accuracy.png` - Main performance dashboard
- `confusion_matrix.png` - Error analysis
- `performance_metrics.png` - Speed and KB analysis
- `detailed_analysis.png` - Deep dive charts
- `summary_report.txt` - Text report

---

## 🚀 **Quick Reference Commands**

```bash
# 1. View test suite stats
python comprehensive_test_cases.py

# 2. Start API server (terminal 1)
python run_api.py

# 3. Run comprehensive tests (terminal 2)
python run_comprehensive_tests.py

# 4. Generate visualizations
python visualize_results.py

# 5. View specific result file
python visualize_results.py comprehensive_test_20260911_143052.json
```

---

## 💡 **Tips for Best Results**

1. **Warm up the system**: Run 1-2 test cases manually before full suite
2. **Stable environment**: Ensure good internet connection for LLM API calls
3. **Fresh start**: Restart API server before major test runs
4. **Compare over time**: Save results with timestamps to track improvements
5. **Focus on patterns**: Look at category-level accuracy, not individual cases

---

**Happy Testing! 🎯**
