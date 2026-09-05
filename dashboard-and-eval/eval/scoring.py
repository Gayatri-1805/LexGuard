"""
Evaluation Scoring Module

Person C - Dashboard and Evaluation
Computes metrics against gold set:
  - Precision: % of detected hallucinations that are true hallucinations
  - Recall: % of hallucinations in gold set that are detected
  - F1: harmonic mean
  - Confusion matrix, ROC curve, precision-recall curve

Input: verdicts from pipeline.process_claim() on gold_set/
Output: metrics report (JSON, CSV, plots)
"""
