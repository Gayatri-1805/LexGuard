import sys
import os
import time
from pathlib import Path

# Add paths to enable imports
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "api-and-sdk"))
sys.path.insert(0, str(project_root / "dashboard-and-eval"))

from fastapi.testclient import TestClient
from api.main import app

from eval.scoring import load_gold_set, run_eval, compute_metrics, print_report

client = TestClient(app)

def predict_fn(claim_text: str) -> dict:
    try:
        response = client.post("/api/check", json={"text": claim_text, "context": "legal_eval"})
        if response.status_code != 200:
            print(f"  ⚠  HTTP {response.status_code} for claim — treating as NOT_ENOUGH_INFO")
            print(f"     Details: {response.text}")
            return {"label": "NOT_ENOUGH_INFO", "confidence": 0.0}
        
        data = response.json()
        verdicts = data.get("verdicts", [])
        if verdicts:
            first_verdict = verdicts[0]
            label = first_verdict.get("label", "NOT_ENOUGH_INFO")
            confidence = first_verdict.get("confidence") or 0.5
        else:
            decision = data.get("decision", "ABSTAIN")
            label_map = {"SAFE": "ENTAILED", "FLAGGED": "CONTRADICTED", "ABSTAIN": "NOT_ENOUGH_INFO"}
            label = label_map.get(decision, "NOT_ENOUGH_INFO")
            confidence = data.get("trust_index", 0.5)

        return {"label": label, "confidence": float(confidence)}

    except Exception as e:
        print(f"  ⚠  API call failed: {e}")
        return {"label": "NOT_ENOUGH_INFO", "confidence": 0.0}

def main():
    gold_set_path = "dashboard-and-eval/eval/gold_set/gold_set.jsonl"
    gold_items = load_gold_set(gold_set_path)
    
    # We only want to evaluate a small subset first to check if the new pipeline works as intended
    # Evaluate 10 items to save time/tokens unless directed otherwise.
    sample = gold_items[:10]
    
    print(f"\n🚀 Running eval on {len(sample)} gold items (Sample)...\n")
    start = time.time()
    results = run_eval(sample, predict_fn=predict_fn, skip_nei=False)
    elapsed = time.time() - start
    print(f"\n⏱  Completed in {elapsed:.1f}s\n")
    
    metrics = compute_metrics(results)
    print_report(metrics)

if __name__ == "__main__":
    main()
