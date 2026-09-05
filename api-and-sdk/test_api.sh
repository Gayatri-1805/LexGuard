#!/bin/bash

# Test script for FastAPI hallucination detection service
# Starts server, tests endpoints, then stops

set -e

echo "=========================================="
echo "Testing Hallucination Detection API"
echo "=========================================="
echo ""

# Start the server in background
echo "Starting API server on port 8000..."
python -m uvicorn api.main:app --port 8000 > /tmp/api.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test 1: Health endpoint
echo ""
echo "Test 1: GET /health"
curl -s http://localhost:8000/health | jq '.'

# Test 2: POST /check with sample text
echo ""
echo "Test 2: POST /check with sample text"
RESPONSE=$(curl -s -X POST http://localhost:8000/api/check \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Section 43A requires data protection measures.",
    "context": "Legal analysis"
  }')

echo "$RESPONSE" | jq '.'

# Extract request_id from response
REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id')
echo ""
echo "Request ID: $REQUEST_ID"

# Wait a bit for background task to complete
sleep 2

# Test 3: GET /analytics/summary
echo ""
echo "Test 3: GET /analytics/summary"
curl -s http://localhost:8000/api/analytics/summary?days=30 | jq '.'

# Test 4: GET /analytics/checks
echo ""
echo "Test 4: GET /analytics/checks"
curl -s http://localhost:8000/api/analytics/checks?limit=10 | jq '.'

# Test 5: GET /analytics/flagged
echo ""
echo "Test 5: GET /analytics/flagged"
curl -s http://localhost:8000/api/analytics/flagged?limit=10 | jq '.'

# Stop the server
echo ""
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true

echo ""
echo "=========================================="
echo "✓ All tests completed!"
echo "=========================================="
