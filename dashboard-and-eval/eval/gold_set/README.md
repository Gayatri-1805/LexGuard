# Gold Standard Evaluation Set

Person C - Dashboard and Evaluation

Directory for hand-labeled ground truth claims:
- hallucinated_claims.json: claims that contain known hallucinations
- credible_claims.json: verified true legal claims
- disputed_claims.json: claims with ambiguous or uncertain ground truth

Format: List of {claim, label, source, jurisdiction, explanation}
Used by scoring.py for evaluation metrics (precision, recall, F1).
