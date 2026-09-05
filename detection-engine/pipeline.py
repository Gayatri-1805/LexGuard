"""
Detection Pipeline Orchestrator

Person A - Detection Engine
Coordinates the full hallucination detection flow:
  1. Decompose -> 2. Filter -> 3. Ground -> 4. Metamorphic -> 5. Trust Score

Main entry point: process_claim(claim: Claim) -> Verdict

Logs pipeline execution metrics and traces for debugging.
"""
