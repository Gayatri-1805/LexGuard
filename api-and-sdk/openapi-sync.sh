#!/bin/bash

# Sync OpenAPI schema and generate TypeScript types
#
# This script:
# 1. Starts the FastAPI app briefly to extract OpenAPI schema
# 2. Saves the schema to openapi.json
# 3. Runs openapi-typescript to generate TypeScript types
# 4. Copies types to sdk-npm/src/generated-types.ts
#
# When to run:
#   - After changing request/response schemas in shared/schemas.py or api/routes/*
#   - Before running npm build for sdk-npm
#   - Commit both openapi.json and sdk-npm/src/generated-types.ts to version control
#
# Prerequisites:
#   - Python FastAPI app set up (api/main.py)
#   - Node.js and openapi-typescript installed
#   - uvicorn available for starting the API

set -e

echo "=========================================="
echo "OpenAPI Schema & TypeScript Types Sync"
echo "=========================================="
echo ""

# Check prerequisites
if ! command -v python &> /dev/null; then
    echo "✗ Python not found. Please install Python 3.10+."
    exit 1
fi

if ! command -v npx &> /dev/null; then
    echo "✗ npx not found. Please install Node.js."
    exit 1
fi

echo "Generating OpenAPI schema from FastAPI app..."

# Use Python to extract OpenAPI schema without starting a server
python -c "
import json
from api.main import app

# Get OpenAPI schema
schema = app.openapi()

# Write to file
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

print('✓ Schema saved to openapi.json')
"

echo ""
echo "Generating TypeScript types from schema..."

# Generate TypeScript types using openapi-typescript
npx openapi-typescript openapi.json -o sdk-npm/src/generated-types.ts

if [ -f "sdk-npm/src/generated-types.ts" ]; then
    echo "✓ TypeScript types generated: sdk-npm/src/generated-types.ts"
    echo ""
    echo "=========================================="
    echo "✓ Sync complete!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  1. Review changes to openapi.json (version control it)"
    echo "  2. Review changes to sdk-npm/src/generated-types.ts (version control it)"
    echo "  3. Build TS client: cd sdk-npm && npm run build"
    echo "  4. Test with: npm run build && npm test"
    echo ""
else
    echo "✗ Failed to generate TypeScript types"
    exit 1
fi
