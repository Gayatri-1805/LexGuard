"""
Stage 4: Trust Score Computation

Person A - Detection Engine
Aggregates evidence from stages 0-3 into a weighted trust score.
Uses weights (w1, w2, w3) from shared.config to produce final verdict:
  - HALLUCINATION: score below gamma_th
  - UNCERTAIN: score between gamma_th and gamma_crit
  - CREDIBLE: score above gamma_crit

Input: MetamorphicResults, GroundedClaim
Output: Verdict with score, category, explanation
"""
