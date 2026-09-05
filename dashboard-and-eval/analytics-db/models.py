"""
SQLAlchemy ORM Models for Analytics

Person C - Dashboard and Evaluation
Defines schema for persisted checks:
  - Check: each API /check call (timestamp, claim, verdict, latency)
  - Claim: the claim text and metadata (source, jurisdiction)
  - Verdict: the hallucination result (score, category, explanation)

Used by analytics endpoints and dashboard queries.
"""
