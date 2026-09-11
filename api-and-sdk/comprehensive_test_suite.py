#!/usr/bin/env python
"""
Comprehensive Test Suite for Legal Hallucination Detection System
================================================================

This test suite evaluates:
1. Claim extraction accuracy
2. KB lookup performance 
3. LLM judge accuracy
4. End-to-end system performance
5. Performance metrics and visualizations
"""

import json
import time
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import defaultdict, Counter

# Add project paths
_API_SDK_ROOT = Path(__file__).resolve().parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
_PROJECT_ROOT = _API_SDK_ROOT.parent
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT, _PROJECT_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from dotenv import load_dotenv
load_dotenv()

# Import system components
from stages.claim_extractor import extract_claims
from stages.kb_lookup import kb_lookup  
from stages.verdict import get_verdict
from shared.schemas import Claim, ClaimType, VerdictLabel

@dataclass
class TestCase:
    """Test case for evaluation"""
    text: str
    expected_claims: int
    expected_decision: str
    category: str
    contains_hallucination: bool
    description: str

@dataclass 
class TestResult:
    """Result of a single test"""
    test_case: TestCase
    actual_claims: int
    actual_decision: str
    trust_index: float
    processing_time: float
    kb_hits: int
    llm_calls: int
    accuracy: float

class LegalHallucinationTester:
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        self.api_base_url = api_base_url
        self.results: List[TestResult] = []
        
        # Test cases covering various scenarios
        self.test_cases = [
            # Correct Legal Statements (Should be SAFE)
            TestCase(
                text="Section 43A of the IT Act provides for compensation for failure to protect data.",
                expected_claims=1,
                expected_decision="SAFE", 
                category="Correct Statutory Reference",
                contains_hallucination=False,
                description="Accurate reference to IT Act Section 43A"
            ),
            TestCase(
                text="The right to privacy is a fundamental right under the Indian Constitution as established in K.S. Puttaswamy v. Union of India.",
                expected_claims=2,
                expected_decision="SAFE",
                category="Correct Case Law",
                contains_hallucination=False,
                description="Accurate privacy rights case reference"
            ),
            TestCase(
                text="Data controllers must implement reasonable security practices under Section 43A.",
                expected_claims=1,
                expected_decision="SAFE",
                category="Correct Procedural",
                contains_hallucination=False,
                description="Accurate security requirements"
            ),
            
            # Hallucinated Statements (Should be FLAGGED)
            TestCase(
                text="Section 43A only applies to government entities and exempts all private companies.",
                expected_claims=2,
                expected_decision="FLAGGED",
                category="Statutory Hallucination",
                contains_hallucination=True,
                description="False limitation of Section 43A scope"
            ),
            TestCase(
                text="The Supreme Court ruled in Miranda v. State that data breaches have no liability under Indian law.",
                expected_claims=2,
                expected_decision="FLAGGED", 
                category="Case Law Hallucination",
                contains_hallucination=True,
                description="Fabricated case and incorrect ruling"
            ),
            TestCase(
                text="Section 43A requires proof of gross negligence and willful intent for any compensation claims.",
                expected_claims=2,
                expected_decision="FLAGGED",
                category="Procedural Hallucination", 
                contains_hallucination=True,
                description="False burden of proof requirements"
            ),
            
            # Ambiguous/Mixed Statements (Should be ABSTAIN)
            TestCase(
                text="Data protection laws may require companies to implement security measures, but the exact requirements vary.",
                expected_claims=2,
                expected_decision="ABSTAIN",
                category="Ambiguous Statement",
                contains_hallucination=False,
                description="Vague but not incorrect statement"
            ),
            TestCase(
                text="While Section 43A provides compensation, the interpretation of 'reasonable security practices' remains subjective.",
                expected_claims=2, 
                expected_decision="ABSTAIN",
                category="Mixed Correct/Unclear",
                contains_hallucination=False,
                description="Partially verifiable claim"
            ),
            
            # Complex Multi-claim Statements
            TestCase(
                text="Section 43A requires compensation for data breaches. The penalty can be up to 5 crore rupees. Companies must notify authorities within 24 hours.",
                expected_claims=3,
                expected_decision="FLAGGED",
                category="Mixed True/False",
                contains_hallucination=True,
                description="Mix of correct and incorrect claims"
            ),
            TestCase(
                text="K.S. Puttaswamy established privacy rights. Section 43A provides data breach compensation. The Personal Data Protection Bill was passed in 2019.",
                expected_claims=3,
                expected_decision="FLAGGED", 
                category="Mixed True/False",
                contains_hallucination=True,
                description="Mix of correct facts and false timeline"
            )
        ]
    
    def test_claim_extraction(self) -> Dict[str, Any]:
        """Test claim extraction accuracy"""
        print("Testing Claim Extraction...")
        extraction_results = []
        
        for test_case in self.test_cases:
            start_time = time.time()
            try:
                claims = extract_claims(test_case.text)
                processing_time = time.time() - start_time
                
                result = {
                    'text': test_case.text[:50] + "...",
                    'expected_claims': test_case.expected_claims,
                    'actual_claims': len(claims),
                    'accuracy': 1.0 if len(claims) == test_case.expected_claims else 0.0,
                    'processing_time': processing_time,
                    'category': test_case.category,
                    'claims_details': [{'text': c.text, 'type': c.type.value} for c in claims]
                }
                extraction_results.append(result)
                
            except Exception as e:
                extraction_results.append({
                    'text': test_case.text[:50] + "...",
                    'expected_claims': test_case.expected_claims,
                    'actual_claims': 0,
                    'accuracy': 0.0,
                    'processing_time': 0.0,
                    'error': str(e),
                    'category': test_case.category
                })
        
        # Calculate metrics
        total_accuracy = np.mean([r['accuracy'] for r in extraction_results])
        avg_processing_time = np.mean([r['processing_time'] for r in extraction_results])
        
        return {
            'overall_accuracy': total_accuracy,
            'avg_processing_time': avg_processing_time,
            'results': extraction_results
        }
    
    def test_kb_lookup_performance(self) -> Dict[str, Any]:
        """Test knowledge base lookup performance"""
        print("Testing KB Lookup Performance...")
        kb_results = []
        
        # Create test claims for KB lookup
        test_texts = [
            "Section 43A provides for compensation",
            "K.S. Puttaswamy v. Union of India established privacy rights", 
            "Fabricated Section 999Z requires impossible things",
            "Non-existent Case v. Nobody decided nothing"
        ]
        
        for text in test_texts:
            try:
                claims = extract_claims(text)
                for claim in claims:
                    start_time = time.time()
                    kb_result = kb_lookup(claim)
                    processing_time = time.time() - start_time
                    
                    result = {
                        'claim_text': claim.text,
                        'hit': kb_result.hit,
                        'best_score': kb_result.best_score,
                        'num_passages': len(kb_result.passages),
                        'processing_time': processing_time
                    }
                    kb_results.append(result)
                    
            except Exception as e:
                kb_results.append({
                    'claim_text': text,
                    'hit': False,
                    'error': str(e),
                    'processing_time': 0.0
                })
        
        # Calculate metrics
        hit_rate = np.mean([r.get('hit', False) for r in kb_results])
        avg_score = np.mean([r.get('best_score', 0.0) for r in kb_results if 'best_score' in r])
        avg_processing_time = np.mean([r['processing_time'] for r in kb_results])
        
        return {
            'hit_rate': hit_rate,
            'avg_similarity_score': avg_score, 
            'avg_processing_time': avg_processing_time,
            'results': kb_results
        }
    
    def test_end_to_end_api(self) -> Dict[str, Any]:
        """Test full end-to-end API performance"""
        print("Testing End-to-End API Performance...")
        api_results = []
        
        for test_case in self.test_cases:
            start_time = time.time()
            try:
                response = requests.post(
                    f"{self.api_base_url}/check",
                    json={"text": test_case.text, "context": "Test case"},
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Calculate accuracy based on expected vs actual decision
                    decision_accuracy = 1.0 if data['decision'] == test_case.expected_decision else 0.0
                    claims_accuracy = 1.0 if len(data['claims']) == test_case.expected_claims else 0.0
                    
                    result = TestResult(
                        test_case=test_case,
                        actual_claims=len(data['claims']),
                        actual_decision=data['decision'],
                        trust_index=data['trust_index'],
                        processing_time=processing_time,
                        kb_hits=sum(1 for v in data['verdicts'] if v['label'] in ['ENTAILED', 'SUPPORTED']),
                        llm_calls=len(data['verdicts']),
                        accuracy=(decision_accuracy + claims_accuracy) / 2
                    )
                    
                else:
                    result = TestResult(
                        test_case=test_case,
                        actual_claims=0,
                        actual_decision="ERROR",
                        trust_index=0.0,
                        processing_time=processing_time,
                        kb_hits=0,
                        llm_calls=0,
                        accuracy=0.0
                    )
                
                api_results.append(result)
                self.results.append(result)
                
            except Exception as e:
                result = TestResult(
                    test_case=test_case,
                    actual_claims=0,
                    actual_decision="ERROR",
                    trust_index=0.0,
                    processing_time=0.0,
                    kb_hits=0,
                    llm_calls=0,
                    accuracy=0.0
                )
                api_results.append(result)
        
        # Calculate overall metrics
        overall_accuracy = np.mean([r.accuracy for r in api_results])
        decision_accuracy = np.mean([1.0 if r.actual_decision == r.test_case.expected_decision else 0.0 for r in api_results])
        avg_processing_time = np.mean([r.processing_time for r in api_results])
        avg_trust_index = np.mean([r.trust_index for r in api_results])
        
        return {
            'overall_accuracy': overall_accuracy,
            'decision_accuracy': decision_accuracy,
            'avg_processing_time': avg_processing_time,
            'avg_trust_index': avg_trust_index,
            'results': api_results
        }
    
    def generate_visualizations(self, results: Dict[str, Any]) -> None:
        """Generate comprehensive visualizations"""
        print("Generating Visualizations...")
        
        plt.style.use('seaborn-v0_8')
        fig = plt.figure(figsize=(20, 16))
        
        # 1. Overall System Performance
        ax1 = plt.subplot(2, 4, 1)
        metrics = ['Claim Extraction', 'KB Lookup Hit Rate', 'Decision Accuracy', 'Overall Accuracy']
        scores = [
            results['claim_extraction']['overall_accuracy'],
            results['kb_lookup']['hit_rate'],
            results['end_to_end']['decision_accuracy'],
            results['end_to_end']['overall_accuracy']
        ]
        
        bars = ax1.bar(metrics, scores, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
        ax1.set_ylim(0, 1)
        ax1.set_ylabel('Accuracy Score')
        ax1.set_title('System Performance Metrics', fontweight='bold')
        ax1.tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, score in zip(bars, scores):
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, 
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 2. Processing Time Analysis
        ax2 = plt.subplot(2, 4, 2)
        components = ['Claim Extraction', 'KB Lookup', 'End-to-End']
        times = [
            results['claim_extraction']['avg_processing_time'],
            results['kb_lookup']['avg_processing_time'], 
            results['end_to_end']['avg_processing_time']
        ]
        
        bars = ax2.bar(components, times, color=['#FFD93D', '#6BCF7F', '#4D96FF'])
        ax2.set_ylabel('Time (seconds)')
        ax2.set_title('Processing Time by Component', fontweight='bold')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add value labels
        for bar, time_val in zip(bars, times):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{time_val:.3f}s', ha='center', va='bottom', fontweight='bold')
        
        # 3. Decision Distribution
        ax3 = plt.subplot(2, 4, 3)
        decisions = [r.actual_decision for r in results['end_to_end']['results']]
        decision_counts = Counter(decisions)
        
        colors = {'SAFE': '#2ECC71', 'FLAGGED': '#E74C3C', 'ABSTAIN': '#F39C12', 'ERROR': '#95A5A6'}
        ax3.pie(decision_counts.values(), labels=decision_counts.keys(), autopct='%1.1f%%',
               colors=[colors.get(k, '#BDC3C7') for k in decision_counts.keys()])
        ax3.set_title('Decision Distribution', fontweight='bold')
        
        # 4. Trust Index Distribution  
        ax4 = plt.subplot(2, 4, 4)
        trust_indices = [r.trust_index for r in results['end_to_end']['results']]
        ax4.hist(trust_indices, bins=10, alpha=0.7, color='#9B59B6', edgecolor='black')
        ax4.set_xlabel('Trust Index')
        ax4.set_ylabel('Frequency')
        ax4.set_title('Trust Index Distribution', fontweight='bold')
        ax4.axvline(np.mean(trust_indices), color='red', linestyle='--', 
                   label=f'Mean: {np.mean(trust_indices):.3f}')
        ax4.legend()
        
        # 5. Category-wise Performance
        ax5 = plt.subplot(2, 4, 5)
        category_performance = defaultdict(list)
        for result in results['end_to_end']['results']:
            category_performance[result.test_case.category].append(result.accuracy)
        
        categories = list(category_performance.keys())
        accuracies = [np.mean(scores) for scores in category_performance.values()]
        
        bars = ax5.barh(categories, accuracies, color=plt.cm.Set3(np.linspace(0, 1, len(categories))))
        ax5.set_xlabel('Accuracy')
        ax5.set_title('Performance by Category', fontweight='bold')
        
        # Add value labels
        for bar, acc in zip(bars, accuracies):
            ax5.text(bar.get_width() + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{acc:.3f}', ha='left', va='center', fontweight='bold')
        
        # 6. KB Hit vs Miss Analysis
        ax6 = plt.subplot(2, 4, 6)
        kb_results = results['kb_lookup']['results']
        hit_scores = [r['best_score'] for r in kb_results if r.get('hit', False)]
        miss_scores = [r.get('best_score', 0.0) for r in kb_results if not r.get('hit', False)]
        
        ax6.hist([hit_scores, miss_scores], bins=15, alpha=0.7, 
                label=['KB Hits', 'KB Misses'], color=['#27AE60', '#E67E22'])
        ax6.set_xlabel('Similarity Score')
        ax6.set_ylabel('Frequency')
        ax6.set_title('KB Lookup Score Distribution', fontweight='bold')
        ax6.legend()
        
        # 7. Hallucination Detection Performance
        ax7 = plt.subplot(2, 4, 7)
        hallucination_results = []
        non_hallucination_results = []
        
        for result in results['end_to_end']['results']:
            if result.test_case.contains_hallucination:
                # Should be FLAGGED
                correct = result.actual_decision == 'FLAGGED'
                hallucination_results.append(1 if correct else 0)
            else:
                # Should be SAFE or ABSTAIN
                correct = result.actual_decision in ['SAFE', 'ABSTAIN'] 
                non_hallucination_results.append(1 if correct else 0)
        
        hallucination_acc = np.mean(hallucination_results) if hallucination_results else 0
        non_hallucination_acc = np.mean(non_hallucination_results) if non_hallucination_results else 0
        
        detection_types = ['Hallucination\nDetection', 'Non-Hallucination\nClassification']
        detection_scores = [hallucination_acc, non_hallucination_acc]
        
        bars = ax7.bar(detection_types, detection_scores, color=['#C0392B', '#16A085'])
        ax7.set_ylim(0, 1)
        ax7.set_ylabel('Accuracy')
        ax7.set_title('Hallucination Detection Performance', fontweight='bold')
        
        # Add value labels
        for bar, score in zip(bars, detection_scores):
            ax7.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                    f'{score:.3f}', ha='center', va='bottom', fontweight='bold')
        
        # 8. Performance vs Processing Time
        ax8 = plt.subplot(2, 4, 8)
        processing_times = [r.processing_time for r in results['end_to_end']['results']]
        accuracies = [r.accuracy for r in results['end_to_end']['results']]
        categories = [r.test_case.category for r in results['end_to_end']['results']]
        
        scatter = ax8.scatter(processing_times, accuracies, c=range(len(processing_times)), 
                             cmap='viridis', alpha=0.7, s=100)
        ax8.set_xlabel('Processing Time (seconds)')
        ax8.set_ylabel('Accuracy')
        ax8.set_title('Accuracy vs Processing Time', fontweight='bold')
        
        # Add trend line
        z = np.polyfit(processing_times, accuracies, 1)
        p = np.poly1d(z)
        ax8.plot(processing_times, p(processing_times), "r--", alpha=0.8)
        
        plt.tight_layout()
        plt.savefig('legal_hallucination_detector_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Generate detailed confusion matrix for decisions
        self.generate_confusion_matrix(results['end_to_end']['results'])
    
    def generate_confusion_matrix(self, results: List[TestResult]) -> None:
        """Generate confusion matrix for decision accuracy"""
        expected_decisions = [r.test_case.expected_decision for r in results]
        actual_decisions = [r.actual_decision for r in results]
        
        decisions = sorted(list(set(expected_decisions + actual_decisions)))
        
        # Create confusion matrix
        confusion_matrix = np.zeros((len(decisions), len(decisions)))
        decision_to_idx = {dec: idx for idx, dec in enumerate(decisions)}
        
        for exp, act in zip(expected_decisions, actual_decisions):
            confusion_matrix[decision_to_idx[exp], decision_to_idx[act]] += 1
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(confusion_matrix, annot=True, fmt='g', cmap='Blues',
                   xticklabels=decisions, yticklabels=decisions)
        plt.xlabel('Predicted Decision')
        plt.ylabel('Expected Decision') 
        plt.title('Decision Confusion Matrix', fontweight='bold', fontsize=16)
        plt.tight_layout()
        plt.savefig('decision_confusion_matrix.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def generate_detailed_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive text report"""
        report = []
        report.append("=" * 80)
        report.append("LEGAL HALLUCINATION DETECTION SYSTEM - COMPREHENSIVE TEST REPORT")
        report.append("=" * 80)
        report.append(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Test Cases: {len(self.test_cases)}")
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"Overall System Accuracy: {results['end_to_end']['overall_accuracy']:.1%}")
        report.append(f"Decision Accuracy: {results['end_to_end']['decision_accuracy']:.1%}")
        report.append(f"Claim Extraction Accuracy: {results['claim_extraction']['overall_accuracy']:.1%}")
        report.append(f"KB Lookup Hit Rate: {results['kb_lookup']['hit_rate']:.1%}")
        report.append(f"Average Processing Time: {results['end_to_end']['avg_processing_time']:.3f}s")
        report.append("")
        
        # Detailed Component Analysis
        report.append("COMPONENT ANALYSIS")
        report.append("-" * 40)
        
        # Claim Extraction
        report.append("1. CLAIM EXTRACTION PERFORMANCE")
        report.append(f"   • Accuracy: {results['claim_extraction']['overall_accuracy']:.1%}")
        report.append(f"   • Avg Processing Time: {results['claim_extraction']['avg_processing_time']:.3f}s")
        
        # KB Lookup  
        report.append("2. KNOWLEDGE BASE LOOKUP")
        report.append(f"   • Hit Rate: {results['kb_lookup']['hit_rate']:.1%}")
        report.append(f"   • Avg Similarity Score: {results['kb_lookup']['avg_similarity_score']:.3f}")
        report.append(f"   • Avg Processing Time: {results['kb_lookup']['avg_processing_time']:.3f}s")
        
        # Decision Performance
        report.append("3. DECISION ACCURACY")
        report.append(f"   • Overall Decision Accuracy: {results['end_to_end']['decision_accuracy']:.1%}")
        
        # Category Performance
        report.append("\nCATEGORY-WISE PERFORMANCE")
        report.append("-" * 40)
        category_performance = defaultdict(list)
        for result in results['end_to_end']['results']:
            category_performance[result.test_case.category].append(result.accuracy)
        
        for category, accuracies in category_performance.items():
            avg_acc = np.mean(accuracies)
            report.append(f"{category}: {avg_acc:.1%}")
        
        # Hallucination Detection
        report.append("\nHALLUCINATION DETECTION ANALYSIS")  
        report.append("-" * 40)
        hallucination_correct = 0
        hallucination_total = 0
        non_hallucination_correct = 0
        non_hallucination_total = 0
        
        for result in results['end_to_end']['results']:
            if result.test_case.contains_hallucination:
                hallucination_total += 1
                if result.actual_decision == 'FLAGGED':
                    hallucination_correct += 1
            else:
                non_hallucination_total += 1 
                if result.actual_decision in ['SAFE', 'ABSTAIN']:
                    non_hallucination_correct += 1
        
        hall_acc = hallucination_correct / hallucination_total if hallucination_total > 0 else 0
        non_hall_acc = non_hallucination_correct / non_hallucination_total if non_hallucination_total > 0 else 0
        
        report.append(f"Hallucination Detection Rate: {hall_acc:.1%} ({hallucination_correct}/{hallucination_total})")
        report.append(f"True Negative Rate: {non_hall_acc:.1%} ({non_hallucination_correct}/{non_hallucination_total})")
        
        # Performance Recommendations
        report.append("\nRECOMMENDATIONS")
        report.append("-" * 40)
        
        if results['kb_lookup']['hit_rate'] < 0.7:
            report.append("• Consider expanding the knowledge base with more legal documents")
        
        if results['end_to_end']['avg_processing_time'] > 2.0:
            report.append("• Optimize processing pipeline for better performance")
            
        if hall_acc < 0.8:
            report.append("• Fine-tune hallucination detection thresholds")
            
        if results['claim_extraction']['overall_accuracy'] < 0.9:
            report.append("• Improve claim extraction prompt engineering")
        
        report_text = "\n".join(report)
        
        # Save report
        with open('legal_hallucination_test_report.txt', 'w') as f:
            f.write(report_text)
        
        return report_text
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all tests and generate comprehensive results"""
        print("🚀 Starting Comprehensive Legal Hallucination Detection System Tests")
        print("=" * 80)
        
        # Run individual component tests
        claim_results = self.test_claim_extraction()
        kb_results = self.test_kb_lookup_performance() 
        api_results = self.test_end_to_end_api()
        
        # Compile all results
        all_results = {
            'claim_extraction': claim_results,
            'kb_lookup': kb_results,
            'end_to_end': api_results,
            'timestamp': datetime.now().isoformat()
        }
        
        # Generate visualizations
        self.generate_visualizations(all_results)
        
        # Generate detailed report
        report = self.generate_detailed_report(all_results)
        print("\n" + report)
        
        # Save results to JSON
        with open('test_results.json', 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print("\n🎯 Tests completed! Check generated files:")
        print("   • legal_hallucination_detector_performance.png")
        print("   • decision_confusion_matrix.png") 
        print("   • legal_hallucination_test_report.txt")
        print("   • test_results.json")
        
        return all_results

if __name__ == "__main__":
    # Install required packages if not available
    try:
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
    except ImportError:
        print("Installing required packages for visualization...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "matplotlib", "seaborn", "pandas", "numpy"], check=True)
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd
    
    # Run comprehensive tests
    tester = LegalHallucinationTester()
    results = tester.run_comprehensive_tests()