#!/usr/bin/env python
"""
Test Legal Hallucination Detection System with Specific IT Act Cases
==================================================================

Testing the system's ability to detect:
1. Completely hallucinated statements
2. Partially hallucinated statements  
3. Completely accurate statements

From the Information Technology Act, 2000
"""

import json
import requests
import time
from typing import Dict, List, Any
from dataclasses import dataclass
from uuid import uuid4

@dataclass
class ITActTestCase:
    """Test case for IT Act verification"""
    text: str
    context: str
    request_id: str
    expected_category: str  # "hallucinated", "partially_hallucinated", "accurate"
    expected_decision: str  # "FLAGGED", "ABSTAIN", "SAFE"
    description: str

class ITActTester:
    def __init__(self, api_base_url: str = "http://localhost:8000/api"):
        self.api_base_url = api_base_url
        
        # Define test cases based on your examples
        self.test_cases = [
            # HALLUCINATED CASES
            ITActTestCase(
                text="Section 43 of the Information Technology Act, 2000 provides that a person who accesses a computer without permission is automatically sentenced to imprisonment for up to five years and a fine of up to ten lakh rupees. The section also empowers the police to arrest the offender without a warrant.",
                context="Verify this statement against the Information Technology Act, 2000, particularly Section 43.",
                request_id="itact_sec43_001",
                expected_category="hallucinated",
                expected_decision="FLAGGED",
                description="Section 43 is civil liability, not criminal - incorrect imprisonment/fine claims"
            ),
            
            ITActTestCase(
                text="Section 66 of the Information Technology Act, 2000 deals exclusively with cyber terrorism. It provides that anyone who threatens India's sovereignty through a computer network shall receive imprisonment for life as the mandatory punishment, without any requirement of dishonest or fraudulent intent.",
                context="Verify this statement against the Information Technology Act, 2000, particularly Section 66 and the provisions concerning cyber terrorism.",
                request_id="itact_sec66_hallucinated_002", 
                expected_category="hallucinated",
                expected_decision="FLAGGED",
                description="Section 66 is about computer-related offenses, not cyber terrorism; incorrect punishment"
            ),
            
            # PARTIALLY HALLUCINATED CASES
            ITActTestCase(
                text="Section 67 of the Information Technology Act, 2000 punishes the publishing or transmitting of obscene material in electronic form. On the first conviction, the punishment may extend to three years' imprisonment and a fine up to five lakh rupees. For a second or subsequent conviction, imprisonment may extend to seven years and the fine may extend to ten lakh rupees.",
                context="Verify the statement against Section 67 of the Information Technology Act, 2000, including the punishment prescribed for first and subsequent convictions.",
                request_id="itact_sec67_partial_003",
                expected_category="partially_hallucinated", 
                expected_decision="ABSTAIN",
                description="Correct about obscene material, but punishment details may be inaccurate"
            ),
            
            ITActTestCase(
                text="Section 67A of the Information Technology Act, 2000 deals with publishing or transmitting material containing sexually explicit acts or conduct in electronic form. On first conviction, the punishment may extend to five years' imprisonment and a fine up to ten lakh rupees, while a subsequent conviction may result in imprisonment up to seven years and a fine up to twenty lakh rupees.",
                context="Verify this statement against Section 67A of the Information Technology Act, 2000, especially the punishment for first and subsequent convictions.",
                request_id="itact_sec67a_partial_004",
                expected_category="partially_hallucinated",
                expected_decision="ABSTAIN", 
                description="Correct about sexually explicit material, but punishment amounts may be wrong"
            ),
            
            # COMPLETELY ACCURATE CASES
            ITActTestCase(
                text="Section 10A of the Information Technology Act, 2000 provides that where, in the formation of a contract, proposals, acceptances, revocations of proposals or acceptances are expressed in electronic form or by means of electronic records, the contract shall not be deemed to be unenforceable solely because electronic form or electronic records were used.",
                context="Verify this statement against Section 10A of the Information Technology Act, 2000 concerning the validity of contracts formed through electronic means.",
                request_id="itact_sec10a_correct_005",
                expected_category="accurate",
                expected_decision="SAFE",
                description="Accurate statement about electronic contract validity"
            ),
            
            ITActTestCase(
                text="Section 67 of the Information Technology Act, 2000 provides that whoever publishes or transmits, or causes to be published or transmitted, in electronic form any material which is lascivious or appeals to the prurient interest, or whose effect tends to deprave and corrupt persons likely to read, see or hear it, shall be punished on first conviction with imprisonment which may extend to three years and with a fine which may extend to five lakh rupees. In the event of a second or subsequent conviction, imprisonment may extend to five years and the fine may extend to ten lakh rupees.",
                context="Verify this statement against Section 67 of the Information Technology Act, 2000 concerning punishment for publishing or transmitting obscene material in electronic form.",
                request_id="itact_sec67_correct_008",
                expected_category="accurate", 
                expected_decision="SAFE",
                description="Accurate statement about Section 67 obscene material provisions"
            )
        ]
    
    def test_single_case(self, test_case: ITActTestCase) -> Dict[str, Any]:
        """Test a single IT Act case"""
        print(f"\n🔍 Testing: {test_case.request_id}")
        print(f"Expected: {test_case.expected_category} → {test_case.expected_decision}")
        print(f"Description: {test_case.description}")
        
        start_time = time.time()
        
        try:
            # Generate unique request ID to avoid DB constraint errors
            unique_request_id = f"{test_case.request_id}_{int(time.time())}"
            
            response = requests.post(
                f"{self.api_base_url}/check",
                json={
                    "text": test_case.text,
                    "context": test_case.context,
                    "request_id": unique_request_id
                },
                headers={"Content-Type": "application/json"},
                timeout=120  # Increased from 30 to 120 seconds
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyze the result
                actual_decision = data['decision']
                trust_index = data['trust_index']
                claims_count = len(data['claims'])
                verdicts = data['verdicts']
                
                # Determine if the system got it right
                decision_correct = (actual_decision == test_case.expected_decision)
                
                # Calculate accuracy score
                accuracy = 1.0 if decision_correct else 0.0
                
                # Analyze verdicts for insights
                verdict_labels = [v['label'] for v in verdicts]
                kb_hits = sum(1 for v in verdicts if v['label'] in ['ENTAILED', 'SUPPORTED', 'PARTIALLY_SUPPORTED'])
                contradicted = sum(1 for v in verdicts if v['label'] == 'CONTRADICTED')
                unverifiable = sum(1 for v in verdicts if v['label'] == 'UNVERIFIABLE')
                
                result = {
                    'test_case': test_case,
                    'response_data': data,
                    'actual_decision': actual_decision,
                    'expected_decision': test_case.expected_decision,
                    'trust_index': trust_index,
                    'decision_correct': decision_correct,
                    'accuracy': accuracy,
                    'processing_time': processing_time,
                    'claims_count': claims_count,
                    'verdict_labels': verdict_labels,
                    'kb_hits': kb_hits,
                    'contradicted_claims': contradicted,
                    'unverifiable_claims': unverifiable,
                    'status': 'success'
                }
                
                # Print immediate results
                status_icon = "✅" if decision_correct else "❌"
                print(f"{status_icon} Result: {actual_decision} (Trust: {trust_index:.3f})")
                print(f"   Claims: {claims_count}, KB Hits: {kb_hits}, Contradicted: {contradicted}")
                print(f"   Processing Time: {processing_time:.3f}s")
                
                return result
                
            else:
                error_result = {
                    'test_case': test_case,
                    'actual_decision': 'ERROR',
                    'expected_decision': test_case.expected_decision,
                    'decision_correct': False,
                    'accuracy': 0.0,
                    'processing_time': processing_time,
                    'status': 'error',
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                print(f"❌ Error: HTTP {response.status_code}")
                return error_result
                
        except Exception as e:
            error_result = {
                'test_case': test_case,
                'actual_decision': 'ERROR', 
                'expected_decision': test_case.expected_decision,
                'decision_correct': False,
                'accuracy': 0.0,
                'processing_time': 0.0,
                'status': 'error',
                'error': str(e)
            }
            print(f"❌ Exception: {e}")
            return error_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all IT Act test cases"""
        print("🚀 Testing Legal Hallucination Detection on IT Act Cases")
        print("=" * 70)
        
        results = []
        category_results = {"hallucinated": [], "partially_hallucinated": [], "accurate": []}
        
        for test_case in self.test_cases:
            result = self.test_single_case(test_case)
            results.append(result)
            category_results[test_case.expected_category].append(result)
        
        # Calculate overall metrics
        total_accuracy = sum(r['accuracy'] for r in results) / len(results)
        avg_processing_time = sum(r['processing_time'] for r in results) / len(results)
        
        # Calculate category-specific metrics
        category_metrics = {}
        for category, cat_results in category_results.items():
            if cat_results:
                category_metrics[category] = {
                    'accuracy': sum(r['accuracy'] for r in cat_results) / len(cat_results),
                    'count': len(cat_results),
                    'avg_trust_index': sum(r.get('trust_index', 0) for r in cat_results) / len(cat_results)
                }
        
        # Generate summary report
        print("\n" + "=" * 70)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 70)
        
        print(f"Overall Accuracy: {total_accuracy:.1%}")
        print(f"Average Processing Time: {avg_processing_time:.3f}s")
        print(f"Total Test Cases: {len(results)}")
        
        print("\n📈 CATEGORY BREAKDOWN:")
        for category, metrics in category_metrics.items():
            print(f"  {category.upper()}:")
            print(f"    • Accuracy: {metrics['accuracy']:.1%}")
            print(f"    • Cases: {metrics['count']}")
            print(f"    • Avg Trust Index: {metrics['avg_trust_index']:.3f}")
        
        # Detailed analysis
        print("\n🔬 DETAILED ANALYSIS:")
        
        # Hallucination Detection Performance
        hallucinated_results = category_results["hallucinated"]
        hallucination_detection_rate = sum(1 for r in hallucinated_results if r['actual_decision'] == 'FLAGGED') / len(hallucinated_results) if hallucinated_results else 0
        print(f"  Hallucination Detection Rate: {hallucination_detection_rate:.1%}")
        
        # Accurate Statement Recognition
        accurate_results = category_results["accurate"] 
        accurate_recognition_rate = sum(1 for r in accurate_results if r['actual_decision'] == 'SAFE') / len(accurate_results) if accurate_results else 0
        print(f"  Accurate Statement Recognition: {accurate_recognition_rate:.1%}")
        
        # Partial Hallucination Handling
        partial_results = category_results["partially_hallucinated"]
        partial_abstain_rate = sum(1 for r in partial_results if r['actual_decision'] == 'ABSTAIN') / len(partial_results) if partial_results else 0
        print(f"  Partial Hallucination Abstain Rate: {partial_abstain_rate:.1%}")
        
        # Knowledge Base Performance
        total_kb_hits = sum(r.get('kb_hits', 0) for r in results)
        total_claims = sum(r.get('claims_count', 0) for r in results)
        kb_hit_rate = total_kb_hits / total_claims if total_claims > 0 else 0
        print(f"  Knowledge Base Hit Rate: {kb_hit_rate:.1%}")
        
        # Generate detailed case-by-case results
        print(f"\n📋 CASE-BY-CASE RESULTS:")
        for i, result in enumerate(results, 1):
            test_case = result['test_case']
            status_icon = "✅" if result['decision_correct'] else "❌"
            print(f"{i}. {status_icon} {test_case.request_id}")
            print(f"   Expected: {test_case.expected_decision} | Actual: {result['actual_decision']}")
            print(f"   Trust Index: {result.get('trust_index', 0):.3f} | Time: {result['processing_time']:.3f}s")
        
        # Compile final results
        final_results = {
            'overall_accuracy': total_accuracy,
            'avg_processing_time': avg_processing_time,
            'category_metrics': category_metrics,
            'hallucination_detection_rate': hallucination_detection_rate,
            'accurate_recognition_rate': accurate_recognition_rate,
            'partial_abstain_rate': partial_abstain_rate,
            'kb_hit_rate': kb_hit_rate,
            'individual_results': results,
            'timestamp': time.time()
        }
        
        # Save results
        with open('it_act_test_results.json', 'w') as f:
            json.dump(final_results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: it_act_test_results.json")
        
        return final_results

if __name__ == "__main__":
    tester = ITActTester()
    results = tester.run_all_tests()