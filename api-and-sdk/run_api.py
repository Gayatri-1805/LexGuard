#!/usr/bin/env python
"""
Run the FastAPI app with proper Python path configuration.

This script ensures that both the api-and-sdk package and the shared
package are importable, regardless of where uvicorn is called from.

Usage:
  python run_api.py
"""

import sys
from pathlib import Path

# Add api-and-sdk to path (for api package)
api_and_sdk_dir = Path(__file__).parent
sys.path.insert(0, str(api_and_sdk_dir))

# Add project root to path (for shared package)
project_root = api_and_sdk_dir.parent
sys.path.insert(0, str(project_root))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(api_and_sdk_dir)],
    )
