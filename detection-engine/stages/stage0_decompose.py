"""
Stage 0: Decompose

Person A - Detection Engine
Breaks down a claim into sub-claims and identified entities.
Uses LLM judge to structure the claim for downstream analysis.

Input: Claim (string)
Output: DecomposedClaim with sub_claims list, identified_entities dict
"""
