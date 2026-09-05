"""
Configuration and environment variable management.

Loads from .env:
  - JUDGE_MODEL: name of the LLM judge (e.g., "claude-3-opus")
  - TRUST_WEIGHTS: w1, w2, w3 (weights for trust score stages)
  - GAMMA_THRESHOLD: decision threshold for hallucination detection
  - GAMMA_CRITICAL: critical confidence threshold
  - POSTGRES_URL, QDRANT_URL: database connection strings
  - API_PORT, API_HOST: API server settings

Provides defaults for all values if env vars not set.
"""
