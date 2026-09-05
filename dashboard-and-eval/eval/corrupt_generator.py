"""
Corruption Generator for Evaluation

Person C - Dashboard and Evaluation
Generates synthetic hallucinated claims by applying transformations
(fact substitution, entity swaps, negation flips) to credible claims.

Used to expand evaluation set and test hallucination detection robustness.

Functions:
  - corrupt_fact(claim: str, field: str) -> str
  - corrupt_entity(claim: str, entity_type: str) -> str
  - negate_claim(claim: str) -> str
"""
