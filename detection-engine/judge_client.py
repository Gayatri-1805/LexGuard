"""
Judge Client for LLM Calls

Person A - Detection Engine
Wrapper for LLM judge API calls (e.g., OpenAI, Anthropic).
Handles prompt engineering, retries, and structured output parsing
for all stages (decompose, filter, metamorphic analysis, etc.).

Configured via shared.config.JUDGE_MODEL.
"""
