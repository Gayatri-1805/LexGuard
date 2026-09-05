"""
Stage 1: Filter

Person A - Detection Engine
Filters out non-falsifiable or trivial claims.
Focuses hallucination detection on claims that can be grounded against
legal knowledge bases.

Input: DecomposedClaim
Output: FilteredClaim (subset of sub_claims flagged for grounding)
"""
