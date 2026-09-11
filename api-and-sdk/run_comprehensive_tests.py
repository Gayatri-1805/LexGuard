"""
Comprehensive Test Runner for Legal Hallucination Detection
===========================================================

Runs all test cases and generates detailed metrics, including:
- Overall accuracy
- Per-category accuracy
- Per-difficulty accuracy  
- Confusion matrix
- Detailed per-case analysis
- Performance metrics (latency, KB hits)
- Export to JSON and CSV for visualization
"""

import requests
import time
import json
from datetime import datetime
from typing import Dict, List
from comprehensive_test_cases import COMPREHENSIVE_TEST_CASES, get_test_statistics

API_URL = "http://localhost:8000/api/check"
TIMEOUT = 120  # 2 minutes per request

class TestResult:
    """Stores result of a single test case."""
    def __init__(self, test_case, response_data, processing_time, error=None):
        self.test_id = test_case['id']
        self.category = test_case['category']
        self.difficulty = test_case.get('difficulty', 'unknown')
        self.expected = test_case['expected_decision']
        self.error = error
        
        if error:
            self.actual = 'ERROR'
            self.correct = False
            self.trust_index = 0.0
            self.claims_count = 0
            self.kb_hits = 0
            self.contradicted = 0
        else:
            self.actual = response_data.get('decision', 'UNKNOWN')
            self.correct = (self.actual == self.expected)
            self.trust_index = response_data.get('trust_index', 0.0)
            
            verdicts = response_data.get('verdicts', [])
            self.claims_count = len(response_data.get('claims', []))
            self.kb_hits = sum(1 for v in verdicts if v.get('label') in ['ENTAILED', 'SUPPORTED', 'PARTIALLY_SUPPORTED'])
            self.contradicted = sum(1 for v in verdicts if v.get('label') == 'CONTRADICTED')
        
        self.processing_time = processing_time
        self.description = test_case.get('description', '')

def run_single_test(test_case: Dict) -> TestResult:
    """Run a single test case against the API."""
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json={'text': test_case['text'], 'context': 'comprehensive_test'},
            timeout=TIMEOUT
        )
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            return TestResult(test_case, response.json(), processing_time)
        else:
            return TestResult(test_case, {}, processing_time, error=f"HTTP {response.status_code}")
            
    except requests.exceptions.Timeout:
        processing_time = time.time() - start_time
        return TestResult(test_case, {}, processing_time, error="Timeout")
    except Exception as e:
        processing_time = time.time() - start_time
        return TestResult(test_case, {}, processing_time, error=str(e))

def calculate_metrics(results: List[TestResult]) -> Dict:
    """Calculate comprehensive metrics from test results."""
    
    total = len(results)
    correct = sum(1 for r in results if r.correct)
    
    # Overall metrics
    metrics = {
        'total_cases': total,
        'correct': correct,
        'accuracy': correct / total if total > 0 else 0.0,
        'errors': sum(1 for r in results if r.error),
    }
    
    # Per-category metrics
    categories = {}
    for result in results:
        cat = result.category
        if cat not in categories:
            categories[cat] = {'total': 0, 'correct': 0, 'results': []}
        categories[cat]['total'] += 1
        if result.correct:
            categories[cat]['correct'] += 1
        categories[cat]['results'].append(result)
    
    for cat in categories:
        categories[cat]['accuracy'] = (
            categories[cat]['correct'] / categories[cat]['total']
            if categories[cat]['total'] > 0 else 0.0
        )
    
    metrics['by_category'] = categories
    
    # Per-difficulty metrics
    difficulties = {}
    for result in results:
        diff = result.difficulty
        if diff not in difficulties:
            difficulties[diff] = {'total': 0, 'correct': 0}
        difficulties[diff]['total'] += 1
        if result.correct:
            difficulties[diff]['correct'] += 1
    
    for diff in difficulties:
        difficulties[diff]['accuracy'] = (
            difficulties[diff]['correct'] / difficulties[diff]['total']
            if difficulties[diff]['total'] > 0 else 0.0
        )
    
    metrics['by_difficulty'] = difficulties
    
    # Confusion matrix
    confusion = {}
    for result in results:
        key = f"{result.expected} → {result.actual}"
        confusion[key] = confusion.get(key, 0) + 1
    
    metrics['confusion_matrix'] = confusion
    
    # Performance metrics
    metrics['avg_processing_time'] = sum(r.processing_time for r in results) / total if total > 0 else 0.0
    metrics['avg_kb_hit_rate'] = sum(r.kb_hits / r.claims_count if r.claims_count > 0 else 0 for r in results) / total if total > 0 else 0.0
    metrics['total_kb_hits'] = sum(r.kb_hits for r in results)
    metrics['total_claims'] = sum(r.claims_count for r in results)
    
    return metrics

def print_results(results: List[TestResult], metrics: Dict):
    """Print formatted test results."""
    
    print("\n" + "=" * 80)
    print("🚀 COMPREHENSIVE TEST RESULTS")
    print("=" * 80)
    
    # Overall summary
    print(f"\n📊 OVERALL SUMMARY")
    print(f"   Total Cases: {metrics['total_cases']}")
    print(f"   Correct: {metrics['correct']}")
    print(f"   Accuracy: {metrics['accuracy']:.1%}")
    print(f"   Errors: {metrics['errors']}")
    print(f"   Avg Processing Time: {metrics['avg_processing_time']:.2f}s")
    print(f"   KB Hit Rate: {metrics['avg_kb_hit_rate']:.1%}")
    
    # Per-category accuracy
    print(f"\n📈 ACCURACY BY CATEGORY")
    for category, data in sorted(metrics['by_category'].items()):
        accuracy = data['accuracy']
        icon = "✅" if accuracy >= 0.8 else "⚠️" if accuracy >= 0.6 else "❌"
        print(f"   {icon} {category:25s}: {data['correct']:2d}/{data['total']:2d} ({accuracy:.1%})")
    
    # Per-difficulty accuracy
    print(f"\n🎯 ACCURACY BY DIFFICULTY")
    for difficulty, data in sorted(metrics['by_difficulty'].items()):
        accuracy = data['accuracy']
        icon = "✅" if accuracy >= 0.8 else "⚠️" if accuracy >= 0.6 else "❌"
        print(f"   {icon} {difficulty:25s}: {data['correct']:2d}/{data['total']:2d} ({accuracy:.1%})")
    
    # Confusion matrix
    print(f"\n🔀 CONFUSION MATRIX")
    for transition, count in sorted(metrics['confusion_matrix'].items(), key=lambda x: -x[1]):
        print(f"   {transition:30s}: {count:2d}")
    
    # Detailed case results
    print(f"\n📋 DETAILED CASE RESULTS")
    print("   " + "-" * 76)
    
    for result in results:
        icon = "✅" if result.correct else "❌" if result.error else "❌"
        print(f"\n   {icon} {result.test_id}")
        print(f"      Expected: {result.expected:10s} | Actual: {result.actual:10s}")
        print(f"      Trust: {result.trust_index:.3f} | Claims: {result.claims_count} | KB Hits: {result.kb_hits} | Contradicted: {result.contradicted}")
        print(f"      Time: {result.processing_time:.2f}s | Difficulty: {result.difficulty}")
        if result.error:
            print(f"      ⚠️  Error: {result.error}")
        print(f"      📝 {result.description}")
    
    print("\n" + "=" * 80)

def export_results(results: List[TestResult], metrics: Dict, output_prefix: str = "comprehensive_test"):
    """Export results to JSON and CSV."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON export with full details
    json_data = {
        'timestamp': timestamp,
        'metrics': metrics,
        'results': [
            {
                'test_id': r.test_id,
                'category': r.category,
                'difficulty': r.difficulty,
                'expected': r.expected,
                'actual': r.actual,
                'correct': r.correct,
                'trust_index': r.trust_index,
                'claims_count': r.claims_count,
                'kb_hits': r.kb_hits,
                'contradicted': r.contradicted,
                'processing_time': r.processing_time,
                'error': r.error,
                'description': r.description
            }
            for r in results
        ]
    }
    
    json_file = f"{output_prefix}_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results exported to: {json_file}")
    
    # CSV export for easy analysis
    csv_file = f"{output_prefix}_{timestamp}.csv"
    with open(csv_file, 'w', encoding='utf-8') as f:
        f.write("test_id,category,difficulty,expected,actual,correct,trust_index,claims,kb_hits,contradicted,time_sec,error\n")
        for r in results:
            f.write(f"{r.test_id},{r.category},{r.difficulty},{r.expected},{r.actual},{r.correct},"
                   f"{r.trust_index},{r.claims_count},{r.kb_hits},{r.contradicted},{r.processing_time:.2f},{r.error or ''}\n")
    
    print(f"💾 CSV exported to: {csv_file}")
    
    return json_file, csv_file

def main():
    """Run all comprehensive tests."""
    
    print("\n" + "=" * 80)
    print("🧪 STARTING COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    
    # Show test statistics
    stats = get_test_statistics()
    print(f"\nTest Suite Overview:")
    print(f"   Total Cases: {stats['total_cases']}")
    print(f"   Categories: {', '.join(stats['by_category'].keys())}")
    print(f"   Difficulties: {', '.join(stats['by_difficulty'].keys())}")
    
    # Verify API is accessible
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        print(f"\n✅ API Server: Accessible")
    except:
        print(f"\n❌ API Server: Not accessible at {API_URL}")
        print(f"   Please start the server: python run_api.py")
        return
    
    print(f"\n🏃 Running {stats['total_cases']} test cases...")
    print("   This may take several minutes...\n")
    
    # Run all tests
    results = []
    for i, test_case in enumerate(COMPREHENSIVE_TEST_CASES, 1):
        print(f"   [{i:2d}/{stats['total_cases']:2d}] Testing {test_case['id']}...", end=' ')
        result = run_single_test(test_case)
        results.append(result)
        
        icon = "✅" if result.correct else "❌"
        print(f"{icon} {result.actual} (expected {result.expected}) - {result.processing_time:.1f}s")
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    
    # Print results
    print_results(results, metrics)
    
    # Export results
    export_results(results, metrics)
    
    # Final grade
    accuracy = metrics['accuracy']
    if accuracy >= 0.9:
        grade = "A+ (Excellent)"
    elif accuracy >= 0.8:
        grade = "A (Very Good)"
    elif accuracy >= 0.7:
        grade = "B (Good)"
    elif accuracy >= 0.6:
        grade = "C (Fair)"
    else:
        grade = "D (Needs Improvement)"
    
    print(f"\n🎯 FINAL GRADE: {grade} ({accuracy:.1%} accuracy)")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
