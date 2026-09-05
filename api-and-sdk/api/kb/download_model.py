"""
Pre-download the BAAI/bge-small-en-v1.5 model from Hugging Face.

This script handles SSL certificate issues and caches the model locally.
Run this once before building the index.

Usage: python -m api.kb.download_model
"""

import os
import ssl
import sys

# Disable SSL verification
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

try:
    from sentence_transformers import SentenceTransformer
    
    print("=" * 70)
    print("Downloading BAAI/bge-small-en-v1.5 embedding model...")
    print("=" * 70 + "\n")
    
    model = SentenceTransformer(
        "BAAI/bge-small-en-v1.5",
        trust_remote_code=True,
        device="cpu"
    )
    
    print("\n" + "=" * 70)
    print("✓ Model downloaded and cached successfully!")
    print("=" * 70)
    print(f"\nModel location: {model.get_sentence_embedding_dimension()} dimensions")
    print("Ready to build index. Run: python -m api.kb.build_index\n")
    
except Exception as e:
    print(f"\n✗ Failed to download model: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
