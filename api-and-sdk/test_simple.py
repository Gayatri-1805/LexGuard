#!/usr/bin/env python
"""Simple test of claim extraction"""

import os
import sys
from pathlib import Path

# Add paths
_API_SDK_ROOT = Path(__file__).resolve().parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print(f"Testing with model: {os.environ.get('JUDGE_MODEL')}")

try:
    from stages.claim_extractor import extract_claims
    result = extract_claims("Section 43A requires data protection.")
    print(f"✓ Success: {len(result)} claims extracted")
    for i, claim in enumerate(result, 1):
        print(f"  {i}. {claim.text}")
except Exception as e:
    print(f"✗ Error: {e}")