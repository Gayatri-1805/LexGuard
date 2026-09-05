#!/bin/bash
# Script to push Legal Hallucination Detector to GitHub
# 
# SETUP REQUIRED FIRST:
# 1. Create repository on GitHub: https://github.com/new
# 2. Note the repository URL
# 3. Replace YOUR_USERNAME below with your actual GitHub username
#
# THEN RUN:
# bash PUSH_TO_GITHUB.sh

set -e

echo "=========================================="
echo "Pushing to GitHub"
echo "=========================================="
echo ""

# Configuration
GITHUB_USERNAME="YOUR_USERNAME"  # ← EDIT THIS
REPO_NAME="legal-hallucination-detector"
REPO_URL="https://github.com/${GITHUB_USERNAME}/${REPO_NAME}.git"

# Verify repository URL
read -p "Repository URL: ${REPO_URL} (y/n)? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "Step 1: Checking git status..."
git status

echo ""
echo "Step 2: Verifying .env is NOT tracked..."
if git ls-files | grep -E "\.env$"; then
    echo "❌ ERROR: .env is tracked in git! Remove with: git rm --cached .env"
    exit 1
else
    echo "✅ .env is properly gitignored"
fi

echo ""
echo "Step 3: Staging all files..."
git add .
git status

echo ""
read -p "Continue with commit? (y/n)? " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "Step 4: Creating commit..."
git commit -m "feat: Initial project structure with API, SDKs, KB, and documentation

- Implemented Person B: FastAPI service with /check and /analytics endpoints
- Implemented KB layer: 115 IT Act sections + 12 case law entries
- Implemented vector retrieval: FAISS index with semantic search
- Implemented SDKs: Python client (httpx) and TypeScript client (fetch)
- Implemented analytics logging: PostgreSQL check_logs table persistence
- Implemented pipeline stub: Ready for Person A integration
- Added comprehensive documentation: Architecture, Getting Started, API, SDKs, Deployment
- Added GitHub Actions CI workflow with 5 job types
- Added Docker Compose stack with PostgreSQL, API, Redis, Qdrant
- All endpoints tested and verified working locally
- v0.1.0 ready for capstone evaluation

Co-authored-by: Team HALO"

echo ""
echo "Step 5: Setting up remote..."
git remote remove origin 2>/dev/null || true
git remote add origin "${REPO_URL}"
git remote -v

echo ""
echo "Step 6: Creating main branch..."
git branch -M main

echo ""
echo "Step 7: Pushing to GitHub..."
git push -u origin main

echo ""
echo "=========================================="
echo "✅ Successfully pushed to GitHub!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Visit: https://github.com/${GITHUB_USERNAME}/${REPO_NAME}"
echo "  2. Enable branch protection (Settings → Branches)"
echo "  3. Create GitHub Release for v0.1.0"
echo "  4. Share with team"
echo ""
echo "Verify CI is running:"
echo "  https://github.com/${GITHUB_USERNAME}/${REPO_NAME}/actions"
echo ""
