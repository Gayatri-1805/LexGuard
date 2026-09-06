"""
Evaluation Scoring Module — Person C

Computes precision, recall, F1, and confusion matrix for the hallucination
detection pipeline against the gold set.

Usage:
    from eval.scoring import load_gold_set, compute_metrics, save_report

    gold = load_gold_set("eval/gold_set/gold_set.jsonl")
    results = run_eval(gold, predict_fn=my_pipeline)
    metrics = compute_metrics(results)
    save_report(metrics, "eval/reports/run_001.json")

Or use the CLI runner:
    python eval/run_eval.py --api-url http://localhost:8000/api --output eval/reports/

Ground truth labels map to binary hallucination detection:
    ENTAILED        → NOT_HALLUCINATED (label=0)
    CONTRADICTED    → HALLUCINATED     (label=1)
    NOT_ENOUGH_INFO → excluded from binary F1, reported separately
"""

import json
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_auc_score,
)
import numpy as np


# ── Type alias ────────────────────────────────────────────────────────────────

GoldItem = dict[str, Any]    # One row from gold_set.jsonl
PredictFn = Callable[[str], dict[str, Any]]  # fn(claim_text) → {"label": str, "confidence": float}


# ── I/O ───────────────────────────────────────────────────────────────────────

def load_gold_set(path: str | Path) -> list[GoldItem]:
    """
    Load the annotated gold set from a JSONL file.

    Each line is a JSON object with at minimum:
        {
            "id":           "gs_001",
            "text":         "Section 43A...",
            "claim_type":   "SECTION_REF",
            "ground_truth": "ENTAILED" | "CONTRADICTED" | "NOT_ENOUGH_INFO"
        }

    Args:
        path: Path to the .jsonl file.

    Returns:
        List of gold item dicts.

    Raises:
        FileNotFoundError if the file does not exist.
        ValueError if any line fails JSON parsing.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Gold set not found: {path}")

    items: list[GoldItem] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"JSON parse error on line {lineno}: {e}") from e

    print(f"📂 Loaded {len(items)} gold items from {path}")
    return items


# ── Eval Runner ───────────────────────────────────────────────────────────────

def run_eval(
    gold_items: list[GoldItem],
    predict_fn: PredictFn,
    skip_nei: bool = False,
) -> list[dict[str, Any]]:
    """
    Run the predict_fn over all gold items and collect results.

    Args:
        gold_items: List of gold set items (from load_gold_set).
        predict_fn: Callable that takes a claim text string and returns a dict:
                    {"label": "ENTAILED"|"CONTRADICTED"|"NOT_ENOUGH_INFO", "confidence": float}
        skip_nei:   If True, skip gold items with ground_truth == NOT_ENOUGH_INFO.

    Returns:
        List of result dicts:
        {
            "id":              str,
            "text":            str,
            "claim_type":      str,
            "ground_truth":    str,
            "predicted_label": str,
            "confidence":      float,
            "correct":         bool,
        }
    """
    results = []
    skipped = 0

    for item in gold_items:
        if skip_nei and item.get("ground_truth") == "NOT_ENOUGH_INFO":
            skipped += 1
            continue

        try:
            prediction = predict_fn(item["text"])
            predicted_label = prediction.get("label", "NOT_ENOUGH_INFO")
            confidence = float(prediction.get("confidence", 0.0))
        except Exception as e:
            print(f"⚠  predict_fn failed on {item['id']}: {e}")
            predicted_label = "NOT_ENOUGH_INFO"
            confidence = 0.0

        results.append({
            "id": item["id"],
            "text": item["text"],
            "claim_type": item.get("claim_type", "OTHER"),
            "ground_truth": item["ground_truth"],
            "predicted_label": predicted_label,
            "confidence": confidence,
            "correct": predicted_label == item["ground_truth"],
        })

    if skipped:
        print(f"ℹ  Skipped {skipped} NOT_ENOUGH_INFO items.")

    print(f"✅ Evaluated {len(results)} items.")
    return results


# ── Metrics ───────────────────────────────────────────────────────────────────

def compute_metrics(results: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute comprehensive evaluation metrics from the results list.

    Metrics:
      - Overall accuracy
      - Per-label precision, recall, F1 (macro and weighted)
      - Confusion matrix
      - Per claim type breakdown
      - Binary hallucination AUC (ENTAILED vs CONTRADICTED, ignoring NOT_ENOUGH_INFO)
      - Stage calibration: mean confidence by correct/incorrect

    Args:
        results: Output of run_eval().

    Returns:
        Metrics dict suitable for JSON serialization.
    """
    y_true = [r["ground_truth"] for r in results]
    y_pred = [r["predicted_label"] for r in results]
    labels = ["ENTAILED", "CONTRADICTED", "NOT_ENOUGH_INFO"]

    # ── Overall accuracy ──────────────────────────────────────────────────────
    correct = sum(r["correct"] for r in results)
    total = len(results)
    accuracy = correct / total if total else 0.0

    # ── Per-label P/R/F1 ──────────────────────────────────────────────────────
    report = classification_report(
        y_true, y_pred, labels=labels, output_dict=True, zero_division=0
    )

    # ── Confusion matrix ──────────────────────────────────────────────────────
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_dict = {
        "labels": labels,
        "matrix": cm.tolist(),
    }

    # ── Binary AUC (ENTAILED vs CONTRADICTED) ─────────────────────────────────
    binary_results = [r for r in results if r["ground_truth"] in ("ENTAILED", "CONTRADICTED")]
    auc_score = None
    if len(binary_results) >= 2:
        try:
            binary_true = [1 if r["ground_truth"] == "CONTRADICTED" else 0 for r in binary_results]
            binary_conf = [
                r["confidence"] if r["predicted_label"] == "CONTRADICTED" else 1 - r["confidence"]
                for r in binary_results
            ]
            if len(set(binary_true)) > 1:
                auc_score = float(roc_auc_score(binary_true, binary_conf))
        except Exception:
            auc_score = None

    # ── Per claim type breakdown ──────────────────────────────────────────────
    claim_types = sorted(set(r["claim_type"] for r in results))
    per_type: dict[str, dict] = {}
    for ct in claim_types:
        ct_results = [r for r in results if r["claim_type"] == ct]
        ct_correct = sum(r["correct"] for r in ct_results)
        per_type[ct] = {
            "total": len(ct_results),
            "correct": ct_correct,
            "accuracy": round(ct_correct / len(ct_results), 4) if ct_results else 0.0,
        }

    # ── Confidence calibration ────────────────────────────────────────────────
    correct_confs = [r["confidence"] for r in results if r["correct"]]
    wrong_confs = [r["confidence"] for r in results if not r["correct"]]
    calibration = {
        "mean_confidence_correct": round(float(np.mean(correct_confs)), 4) if correct_confs else 0.0,
        "mean_confidence_incorrect": round(float(np.mean(wrong_confs)), 4) if wrong_confs else 0.0,
    }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_items": total,
        "accuracy": round(accuracy, 4),
        "macro_f1": round(report.get("macro avg", {}).get("f1-score", 0.0), 4),
        "weighted_f1": round(report.get("weighted avg", {}).get("f1-score", 0.0), 4),
        "binary_auc": round(auc_score, 4) if auc_score is not None else None,
        "per_label": {
            label: {
                "precision": round(report.get(label, {}).get("precision", 0.0), 4),
                "recall": round(report.get(label, {}).get("recall", 0.0), 4),
                "f1": round(report.get(label, {}).get("f1-score", 0.0), 4),
                "support": int(report.get(label, {}).get("support", 0)),
            }
            for label in labels
        },
        "confusion_matrix": cm_dict,
        "per_claim_type": per_type,
        "calibration": calibration,
    }


# ── Report Saving ─────────────────────────────────────────────────────────────

def save_report(
    metrics: dict[str, Any],
    output_path: str | Path,
    also_csv: bool = True,
) -> None:
    """
    Save the metrics report to a JSON file (and optionally a CSV summary).

    Args:
        metrics:     Output of compute_metrics().
        output_path: Path to the output JSON file.
        also_csv:    If True, also write a flat CSV summary alongside the JSON.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # JSON
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"📄 Report saved → {output_path}")

    # CSV summary
    if also_csv:
        csv_path = output_path.with_suffix(".csv")
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            writer.writerow(["timestamp", metrics["timestamp"]])
            writer.writerow(["total_items", metrics["total_items"]])
            writer.writerow(["accuracy", metrics["accuracy"]])
            writer.writerow(["macro_f1", metrics["macro_f1"]])
            writer.writerow(["weighted_f1", metrics["weighted_f1"]])
            writer.writerow(["binary_auc", metrics.get("binary_auc")])
            for label, vals in metrics["per_label"].items():
                writer.writerow([f"{label}_precision", vals["precision"]])
                writer.writerow([f"{label}_recall", vals["recall"]])
                writer.writerow([f"{label}_f1", vals["f1"]])
        print(f"📊 CSV summary saved → {csv_path}")


def print_report(metrics: dict[str, Any]) -> None:
    """Pretty-print the metrics report to stdout."""
    print("\n" + "═" * 60)
    print("  LexGuard Evaluation Report")
    print("═" * 60)
    print(f"  Timestamp:    {metrics['timestamp']}")
    print(f"  Total items:  {metrics['total_items']}")
    print(f"  Accuracy:     {metrics['accuracy']:.1%}")
    print(f"  Macro F1:     {metrics['macro_f1']:.3f}")
    print(f"  Weighted F1:  {metrics['weighted_f1']:.3f}")
    if metrics.get("binary_auc"):
        print(f"  Binary AUC:   {metrics['binary_auc']:.3f}")
    print()
    print("  Per-label breakdown:")
    for label, vals in metrics["per_label"].items():
        print(
            f"    {label:<20} P={vals['precision']:.3f}  R={vals['recall']:.3f}  "
            f"F1={vals['f1']:.3f}  support={vals['support']}"
        )
    print()
    print("  Per claim type accuracy:")
    for ct, vals in metrics["per_claim_type"].items():
        print(f"    {ct:<25} {vals['correct']}/{vals['total']}  ({vals['accuracy']:.1%})")
    print()
    print("  Confidence calibration:")
    c = metrics["calibration"]
    print(f"    Correct predictions:   mean confidence = {c['mean_confidence_correct']:.3f}")
    print(f"    Incorrect predictions: mean confidence = {c['mean_confidence_incorrect']:.3f}")
    print("═" * 60)
