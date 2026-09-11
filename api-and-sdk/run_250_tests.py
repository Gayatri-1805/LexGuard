#!/usr/bin/env python
"""
Run 250 Test Cases Against Legal Hallucination Detection API
==========================================================

This script runs all 250 generated test cases against the API
and generates comprehensive accuracy metrics.
"""

import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict
import sys

class TestRunner:
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        self.api_base_url = api_base_url
        self.results = []
        self.start_time = None
        
    def load_test_cases(self, filename: str) -> List[Dict]:
        """Load test cases from JSON file"""
        print(f"\n📂 Loading test cases from {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        print(f"✓ Loaded {len(cases)} test cases")
        return cases
    
    def test_single_case(self, case: Dict, index: int, total: int) -> Dict[str, Any]:
        """Test a single case"""
        case_id = case['id']
        text = case['text']
        context = case['context']
        expected_decision = case['expected_decision']
        
        # Progress indicator
        if index % 10 == 0:
            print(f"  Testing {index}/{total}: {case_id}")
        
        start_time = time.time()
        
        try:
            # Generate unique request ID
            unique_request_id = f"{case_id}_{int(time.time() * 1000)}"
            
            response = requests.post(
                f"{self.api_base_url}/check",
                json={
                    "text": text,
                    "context": context,
                    "request_id": unique_request_id
                },
                headers={"Content-Type": "application/json"},
                timeout=60  # 60 second timeout per request
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                actual_decision = data['decision']
                trust_index = data['trust_index']
                
                # Determine correctness
                decision_correct = (actual_decision == expected_decision)
                accuracy = 1.0 if decision_correct else 0.0
                
                result = {
                    'id': case_id,
                    'expected_category': case['expected_category'],
                    'expected_decision': expected_decision,
                    'actual_decision': actual_decision,
                    'trust_index': trust_index,
                    'decision_correct': decision_correct,
                    'accuracy': accuracy,
                    'processing_time': processing_time,
                    'claims_count': len(data['claims']),
                    'status': 'success',
                    'section_ref': case.get('section_ref', 'unknown')
                }
                
            else:
                result = {
                    'id': case_id,
                    'expected_category': case['expected_category'],
                    'expected_decision': expected_decision,
                    'actual_decision': 'ERROR',
                    'trust_index': 0.0,
                    'decision_correct': False,
                    'accuracy': 0.0,
                    'processing_time': processing_time,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}",
                    'section_ref': case.get('section_ref', 'unknown')
                }
                
        except requests.Timeout:
            result = {
                'id': case_id,
                'expected_category': case['expected_category'],
                'expected_decision': expected_decision,
                'actual_decision': 'TIMEOUT',
                'trust_index': 0.0,
                'decision_correct': False,
                'accuracy': 0.0,
                'processing_time': 60.0,
                'status': 'timeout',
                'section_ref': case.get('section_ref', 'unknown')
            }
        except Exception as e:
            result = {
                'id': case_id,
                'expected_category': case['expected_category'],
                'expected_decision': expected_decision,
                'actual_decision': 'ERROR',
                'trust_index': 0.0,
                'decision_correct': False,
                'accuracy': 0.0,
                'processing_time': 0.0,
                'status': 'error',
                'error': str(e),
                'section_ref': case.get('section_ref', 'unknown')
            }
        
        return result
    
    def run_all_tests(self, test_cases: List[Dict]) -> Dict[str, Any]:
        """Run all test cases"""
        print("\n🚀 Running 250 Test Cases")
        print("=" * 70)
        
        self.start_time = time.time()
        total = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            result = self.test_single_case(case, i, total)
            self.results.append(result)
            
            # Save intermediate results every 50 cases
            if i % 50 == 0:
                self.save_intermediate_results(i)
        
        total_time = time.time() - self.start_time
        
        # Calculate metrics
        metrics = self.calculate_metrics()
        metrics['total_time'] = total_time
        metrics['avg_time_per_case'] = total_time / len(test_cases)
        
        return metrics
    
    def calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive metrics"""
        print("\n📊 Calculating metrics...")
        
        # Overall metrics
        total_cases = len(self.results)
        successful = [r for r in self.results if r['status'] == 'success']
        timeouts = [r for r in self.results if r['status'] == 'timeout']
        errors = [r for r in self.results if r['status'] == 'error']
        
        overall_accuracy = sum(r['accuracy'] for r in self.results) / total_cases if total_cases > 0 else 0
        
        # Category-wise metrics
        categories = defaultdict(list)
        for result in self.results:
            categories[result['expected_category']].append(result)
        
        category_metrics = {}
        for category, results in categories.items():
            if results:
                category_metrics[category] = {
                    'count': len(results),
                    'accuracy': sum(r['accuracy'] for r in results) / len(results),
                    'avg_trust_index': sum(r['trust_index'] for r in results) / len(results),
                    'avg_processing_time': sum(r['processing_time'] for r in results) / len(results)
                }
        
        # Decision metrics
        decision_breakdown = defaultdict(int)
        for result in self.results:
            decision_breakdown[result['actual_decision']] += 1
        
        # Hallucination detection rate
        hallucinated = [r for r in self.results if r['expected_category'] == 'hallucinated']
        hallucination_detection_rate = sum(1 for r in hallucinated if r['actual_decision'] == 'FLAGGED') / len(hallucinated) if hallucinated else 0
        
        # Accurate recognition rate
        accurate = [r for r in self.results if r['expected_category'] == 'accurate']
        accurate_recognition_rate = sum(1 for r in accurate if r['actual_decision'] == 'SAFE') / len(accurate) if accurate else 0
        
        # Partial handling rate
        partial = [r for r in self.results if r['expected_category'] == 'partially_hallucinated']
        partial_abstain_rate = sum(1 for r in partial if r['actual_decision'] == 'ABSTAIN') / len(partial) if partial else 0
        
        # False positive/negative rates
        false_positives = sum(1 for r in accurate if r['actual_decision'] == 'FLAGGED')
        false_negatives = sum(1 for r in hallucinated if r['actual_decision'] in ['SAFE', 'ABSTAIN'])
        
        false_positive_rate = false_positives / len(accurate) if accurate else 0
        false_negative_rate = false_negatives / len(hallucinated) if hallucinated else 0
        
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'total_cases': total_cases,
            'successful_cases': len(successful),
            'timeout_cases': len(timeouts),
            'error_cases': len(errors),
            'overall_accuracy': overall_accuracy,
            'category_metrics': category_metrics,
            'decision_breakdown': dict(decision_breakdown),
            'hallucination_detection_rate': hallucination_detection_rate,
            'accurate_recognition_rate': accurate_recognition_rate,
            'partial_abstain_rate': partial_abstain_rate,
            'false_positive_rate': false_positive_rate,
            'false_negative_rate': false_negative_rate,
            'precision': (len(hallucinated) - false_negatives) / (len(hallucinated) - false_negatives + false_positives) if (len(hallucinated) - false_negatives + false_positives) > 0 else 0,
            'recall': hallucination_detection_rate,
        }
        
        # Calculate F1 score
        precision = metrics['precision']
        recall = metrics['recall']
        metrics['f1_score'] = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return metrics
    
    def save_intermediate_results(self, count: int):
        """Save intermediate results"""
        filename = f"test_results_250_intermediate_{count}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'results': self.results,
                'count': count,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        print(f"  💾 Saved intermediate results ({count} cases) to {filename}")
    
    def save_final_results(self, metrics: Dict[str, Any]):
        """Save final results"""
        print("\n💾 Saving final results...")
        
        # Save full results
        full_results = {
            'metrics': metrics,
            'individual_results': self.results
        }
        
        filename = f"test_results_250_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(full_results, f, indent=2)
        
        print(f"✓ Saved full results to: {filename}")
        
        # Save summary report
        self.generate_summary_report(metrics, filename)
    
    def generate_summary_report(self, metrics: Dict[str, Any], results_file: str):
        """Generate a text summary report"""
        report = []
        report.append("=" * 70)
        report.append("LEGAL HALLUCINATION DETECTION - 250 TEST CASES SUMMARY")
        report.append("=" * 70)
        report.append(f"Test Date: {metrics['timestamp']}")
        report.append(f"Total Cases: {metrics['total_cases']}")
        report.append(f"Results File: {results_file}")
        report.append("")
        
        report.append("OVERALL PERFORMANCE")
        report.append("-" * 70)
        report.append(f"Overall Accuracy: {metrics['overall_accuracy']:.1%}")
        report.append(f"Successful Tests: {metrics['successful_cases']}/{metrics['total_cases']}")
        report.append(f"Timeouts: {metrics['timeout_cases']}")
        report.append(f"Errors: {metrics['error_cases']}")
        report.append(f"Total Time: {metrics.get('total_time', 0):.1f} seconds")
        report.append(f"Avg Time/Case: {metrics.get('avg_time_per_case', 0):.2f} seconds")
        report.append("")
        
        report.append("CATEGORY PERFORMANCE")
        report.append("-" * 70)
        for category, cat_metrics in metrics['category_metrics'].items():
            report.append(f"{category.upper()}:")
            report.append(f"  • Count: {cat_metrics['count']}")
            report.append(f"  • Accuracy: {cat_metrics['accuracy']:.1%}")
            report.append(f"  • Avg Trust Index: {cat_metrics['avg_trust_index']:.3f}")
            report.append(f"  • Avg Processing Time: {cat_metrics['avg_processing_time']:.2f}s")
        report.append("")
        
        report.append("DETECTION METRICS")
        report.append("-" * 70)
        report.append(f"Hallucination Detection Rate: {metrics['hallucination_detection_rate']:.1%}")
        report.append(f"Accurate Recognition Rate: {metrics['accurate_recognition_rate']:.1%}")
        report.append(f"Partial Abstain Rate: {metrics['partial_abstain_rate']:.1%}")
        report.append(f"False Positive Rate: {metrics['false_positive_rate']:.1%}")
        report.append(f"False Negative Rate: {metrics['false_negative_rate']:.1%}")
        report.append(f"Precision: {metrics['precision']:.1%}")
        report.append(f"Recall: {metrics['recall']:.1%}")
        report.append(f"F1 Score: {metrics['f1_score']:.3f}")
        report.append("")
        
        report.append("DECISION BREAKDOWN")
        report.append("-" * 70)
        for decision, count in metrics['decision_breakdown'].items():
            percentage = count / metrics['total_cases'] * 100
            report.append(f"{decision}: {count} ({percentage:.1f}%)")
        report.append("")
        
        report_text = "\n".join(report)
        print("\n" + report_text)
        
        # Save to file
        report_filename = f"test_report_250_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n✓ Saved summary report to: {report_filename}")

def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("LEGAL HALLUCINATION DETECTION - 250 TEST CASES")
    print("=" * 70)
    
    # Check if API is running
    try:
        # Test with a simple health check via /check endpoint
        response = requests.post(
            "http://localhost:8000/api/check",
            json={"text": "Test", "context": "Health check"},
            timeout=10
        )
        if response.status_code != 200:
            print("\n❌ API is not responding correctly")
            print(f"   Status: {response.status_code}")
            print("   Please ensure the API is running: python run_api.py")
            sys.exit(1)
    except Exception as e:
        print("\n❌ Cannot connect to API at http://localhost:8000")
        print(f"   Error: {e}")
        print("   Please ensure the API is running: python run_api.py")
        sys.exit(1)
    
    print("✓ API is running and accessible")
    
    # Initialize runner
    runner = TestRunner()
    
    # Load test cases
    test_cases = runner.load_test_cases("test_cases_250.json")
    
    # Run all tests
    metrics = runner.run_all_tests(test_cases)
    
    # Save results
    runner.save_final_results(metrics)
    
    print("\n✅ All tests completed!")
    print(f"   Overall Accuracy: {metrics['overall_accuracy']:.1%}")
    print(f"   F1 Score: {metrics['f1_score']:.3f}")

if __name__ == "__main__":
    main()
