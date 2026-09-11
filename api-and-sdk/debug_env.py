#!/usr/bin/env python
"""
Debug script to check environment variables and LLM connection
"""
import os
import sys
from pathlib import Path

# Add paths like the API does
_API_SDK_ROOT = Path(__file__).resolve().parent
_DETECTION_ENGINE_ROOT = _API_SDK_ROOT.parent / "detection-engine"
for _p in (_API_SDK_ROOT, _DETECTION_ENGINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

print("=== Environment Check ===")
print(f"OPENAI_API_KEY: {'SET' if os.environ.get('OPENAI_API_KEY') else 'NOT SET'}")
print(f"OPENAI_BASE_URL: {os.environ.get('OPENAI_BASE_URL', 'NOT SET')}")
print(f"JUDGE_MODEL: {os.environ.get('JUDGE_MODEL', 'NOT SET')}")

# Test available models
try:
    from openai import OpenAI
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL")
    )
    
    print("\nTesting Groq connection and available models...")
    models = client.models.list()
    print(f"✓ Connection successful. Available models:")
    for model in models.data[:10]:  # Show first 10 models
        print(f"  - {model.id}")
    
except Exception as e:
    print(f"✗ Model listing error: {e}")
    import traceback
    traceback.print_exc()

# Test claim extractor import
print(f"\nTesting claim extraction with model: {os.environ.get('JUDGE_MODEL')}...")
try:
    from stages.claim_extractor import extract_claims
    print("✓ claim_extractor imported successfully")
    
    # Test simple extraction
    result = extract_claims("Section 43A requires data protection.")
    print(f"✓ Claim extraction successful: {len(result)} claims extracted")
    for claim in result:
        print(f"  - {claim.text[:50]}...")
        
except ImportError as e:
    print(f"✗ Import error: {e}")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()