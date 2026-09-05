"""
Python SDK Client

Person B - API and SDK
Synchronous and async client for legal-hallucination-detector API.

Main class: HallucinationDetectorClient
  - check(claim: str) -> Verdict
  - check_batch(claims: List[str]) -> List[Verdict]
  - analytics() -> AnalyticsData

Configured via env vars or constructor kwargs (api_url, api_key).
"""
