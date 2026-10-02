"""
Quick script to check progress of running tests
"""
import glob
import json
from datetime import datetime

# Find latest test results file
result_files = glob.glob("test_results_250_*.json")
if result_files:
    latest = max(result_files, key=lambda x: x.split('_')[-1].replace('.json', ''))
    
    with open(latest, 'r') as f:
        data = json.load(f)
    
    completed = len(data.get('results', []))
    total = data.get('total_cases', 250)
    
    print(f"\n📊 Test Progress")
    print(f"=" * 50)
    print(f"Completed: {completed}/{total} ({completed/total*100:.1f}%)")
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    
    if completed > 0:
        results = data['results']
        correct = sum(1 for r in results if r['correct'])
        accuracy = correct / completed * 100
        print(f"Current Accuracy: {accuracy:.1f}%")
        print(f"Correct: {correct}/{completed}")
else:
    print("❌ No test results file found yet. Tests may still be starting...")
