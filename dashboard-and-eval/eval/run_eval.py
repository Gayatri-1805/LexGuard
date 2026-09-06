"""
Evaluation CLI runner — Person C

Calls the LexGuard /api/check endpoint for each gold set item, collects
verdicts, then computes and saves a metrics report.

Usage:
    # Run against live API
    python eval/run_eval.py --api-url http://localhost:8000/api

    # Run against live API, save to custom output dir
    python eval/run_eval.py --api-url http://localhost:8000/api --output eval/reports/

    # Run in dry-run mode (uses a stub predict_fn — no API calls)
    python eval/run_eval.py --dry-run

    # Run only ENTAILED + CONTRADICTED items (skip NOT_ENOUGH_INFO)
    python eval/run_eval.py --api-url http://localhost:8000/api --skip-nei
"""

import argparse
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Allow running from repo root or dashboard-and-eval/
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT))

from eval.scoring import load_gold_set, run_eval, compute_metrics, save_report, print_report  # noqa: E402


# ── API predict function ───────────────────────────────────────────────────────

def make_api_predict_fn(api_url: str, timeout: float = 30.0):
    """
    Create a predict_fn that calls POST /api/check and extracts the verdict.

    The /check endpoint processes full LLM text — for the eval harness we
    send each gold item's claim text as if it were a single-sentence LLM output.

    Returns a callable: fn(claim_text: str) → {"label": str, "confidence": float}
    """
    client = httpx.Client(base_url=api_url, timeout=timeout)

    def predict_fn(claim_text: str) -> dict:
        try:
            response = client.post("/check", json={"text": claim_text, "context": "legal_eval"})
            response.raise_for_status()
            data = response.json()

            # Extract the first verdict's label (single-claim eval)
            verdicts = data.get("verdicts", [])
            if verdicts:
                first_verdict = verdicts[0]
                label = first_verdict.get("label", "NOT_ENOUGH_INFO")
                confidence = first_verdict.get("confidence") or 0.5
            else:
                # No verdicts — map the top-level decision to a label
                decision = data.get("decision", "ABSTAIN")
                label_map = {"SAFE": "ENTAILED", "FLAGGED": "CONTRADICTED", "ABSTAIN": "NOT_ENOUGH_INFO"}
                label = label_map.get(decision, "NOT_ENOUGH_INFO")
                confidence = data.get("trust_index", 0.5)

            return {"label": label, "confidence": float(confidence)}

        except httpx.HTTPStatusError as e:
            print(f"  ⚠  HTTP {e.response.status_code} for claim — treating as NOT_ENOUGH_INFO")
            return {"label": "NOT_ENOUGH_INFO", "confidence": 0.0}
        except Exception as e:
            print(f"  ⚠  API call failed: {e}")
            return {"label": "NOT_ENOUGH_INFO", "confidence": 0.0}

    return predict_fn


# ── Dry-run stub ───────────────────────────────────────────────────────────────

def _stub_predict_fn(claim_text: str) -> dict:
    """
    Stub predict_fn for dry-run testing.
    Returns random (but plausible) predictions without calling any API.
    """
    labels = ["ENTAILED", "CONTRADICTED", "NOT_ENOUGH_INFO"]
    weights = [0.60, 0.25, 0.15]
    label = random.choices(labels, weights=weights)[0]
    confidence = random.uniform(0.55, 0.95)
    return {"label": label, "confidence": confidence}


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="LexGuard Evaluation Runner — evaluates the pipeline against the gold set."
    )
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000/api",
        help="Base URL of the LexGuard API (default: http://localhost:8000/api)",
    )
    parser.add_argument(
        "--gold-set",
        default=str(Path(__file__).parent / "gold_set" / "gold_set.jsonl"),
        help="Path to the gold set JSONL file",
    )
    parser.add_argument(
        "--output",
        default=str(Path(__file__).parent / "reports"),
        help="Output directory for the metrics report (default: eval/reports/)",
    )
    parser.add_argument(
        "--skip-nei",
        action="store_true",
        help="Skip NOT_ENOUGH_INFO items from scoring (binary ENTAILED vs CONTRADICTED only)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use a stub predict function (no API calls — for testing the harness itself)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Seconds to wait between API calls to avoid overwhelming the server (default: 0.1)",
    )
    args = parser.parse_args()

    # Load gold set
    gold_items = load_gold_set(args.gold_set)

    # Build predict function
    if args.dry_run:
        print("🔧 DRY RUN mode — using stub predictions (no API calls)")
        predict_fn = _stub_predict_fn
    else:
        print(f"🌐 API mode — calling {args.api_url}/check")
        predict_fn = make_api_predict_fn(args.api_url)

    # Wrap predict_fn to add delay and progress reporting
    total = len(gold_items)

    def timed_predict_fn(claim_text: str) -> dict:
        result = predict_fn(claim_text)
        if args.delay > 0 and not args.dry_run:
            time.sleep(args.delay)
        return result

    # Run eval
    print(f"\n🚀 Running eval on {total} gold items...\n")
    start = time.time()
    results = run_eval(gold_items, predict_fn=timed_predict_fn, skip_nei=args.skip_nei)
    elapsed = time.time() - start
    print(f"\n⏱  Completed in {elapsed:.1f}s  ({elapsed/max(len(results),1):.2f}s/item)\n")

    # Compute metrics
    metrics = compute_metrics(results)
    print_report(metrics)

    # Save report
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    mode = "dry_run" if args.dry_run else "live"
    report_name = f"eval_{mode}_{ts}"
    output_dir = Path(args.output)
    save_report(metrics, output_dir / f"{report_name}.json", also_csv=True)

    # Also save raw results for debugging
    import json
    results_path = output_dir / f"{report_name}_results.jsonl"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with results_path.open("w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r) + "\n")
    print(f"📋 Raw results saved → {results_path}")


if __name__ == "__main__":
    main()
