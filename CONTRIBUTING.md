# Contributing Guide

Thank you for interest in contributing to the Legal Hallucination Detector! This document outlines the development workflow and guidelines.

---

## Development Setup

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/legal-hallucination-detector.git
cd legal-hallucination-detector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dev dependencies
pip install -e api-and-sdk/
pip install -e api-and-sdk/sdk-python/
pip install pytest pytest-asyncio black flake8 mypy
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your development settings
```

### 3. Initialize Database

```bash
cd api-and-sdk
python -m api.analytics.init_db
python -m api.kb.build_index  # Download model + build index
```

---

## Workflow

### Making Changes

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or: git checkout -b fix/your-bug-name
   ```

2. **Make changes** and test locally:
   ```bash
   python run_api.py  # Start API
   python test_api.py  # Test endpoints
   pytest tests/      # Run unit tests
   ```

3. **Format & lint:**
   ```bash
   black .             # Auto-format code
   flake8 .            # Check style
   mypy .              # Type checking
   ```

4. **Commit with clear message:**
   ```bash
   git commit -m "feat(kb): add semantic search to vector retrieval"
   ```

   Use conventional commits:
   - `feat:` — New feature
   - `fix:` — Bug fix
   - `docs:` — Documentation
   - `test:` — Tests
   - `refactor:` — Code refactoring
   - `perf:` — Performance improvement

5. **Push & create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Code Standards

### Python

- **Style:** Follow PEP 8 via `black`
- **Linting:** `flake8` with max line length 100
- **Type hints:** Required for all functions
- **Docstrings:** Google-style docstrings required

Example:

```python
def lookup_section(self, section_ref: str, act_name: str) -> str | None:
    """
    Retrieve statute section text by exact match.
    
    Args:
        section_ref: Section identifier (e.g., "43A")
        act_name: Act name (e.g., "Information Technology Act, 2000")
    
    Returns:
        Section text if found, else None.
    
    Raises:
        DatabaseError: If database query fails.
    """
    ...
```

### TypeScript

- **Style:** Prettier (run `npm run format`)
- **Linting:** ESLint with strict mode
- **Type checking:** Full type coverage required
- **Async/await:** Preferred over `.then()`

Example:

```typescript
async check(request: CheckRequest): Promise<CheckResponse> {
  /**
   * Check LLM output for hallucinations.
   * 
   * @param request - CheckRequest with text and optional context
   * @returns CheckResponse with claims, verdicts, trust_index
   * @throws DetectorAPIError on API failure
   */
  ...
}
```

### Documentation

- **README:** Top-level overview (1000 words max)
- **ARCHITECTURE.md:** System design and data flow
- **API.md:** Endpoint reference with examples
- **SDK_USAGE.md:** Client library examples
- **Inline comments:** Explain "why", not "what"

---

## Testing

### Unit Tests (Python)

```bash
pytest tests/ -v
pytest tests/test_embeddings.py -v
pytest tests/test_kb.py::test_lookup_section -v
```

Example test:

```python
import pytest
from api.kb.postgres_kb import PostgresKB

@pytest.fixture
def kb():
    return PostgresKB()

def test_lookup_section(kb):
    """Test exact section lookup returns correct text."""
    result = kb.lookup_section("43A", "Information Technology Act, 2000")
    assert result is not None
    assert "compensation" in result.lower()
    assert "data" in result.lower()
```

### Integration Tests

```bash
# Start API: python run_api.py
# In another terminal:
python test_api.py
```

### End-to-End Tests

```python
# tests/test_e2e.py
def test_full_pipeline():
    """Test full flow: check → analytics → verify."""
    # 1. Check endpoint
    response = client.check(text="Section 43A...")
    assert response['decision'] in ['SAFE', 'FLAGGED', 'ABSTAIN']
    
    # 2. Analytics endpoint
    summary = client.get_summary(days=30)
    assert summary['total_checks'] >= 1
    
    # 3. Verify data persisted
    checks = client.get_checks(limit=10)
    assert any(c['request_id'] == response['request_id'] for c in checks['checks'])
```

### Test Coverage

```bash
pytest --cov=api --cov-report=html
# Open htmlcov/index.html in browser
```

---

## Git Workflow

### Branch Naming

- `feature/` — New features
- `fix/` — Bug fixes
- `docs/` — Documentation
- `test/` — Tests
- `refactor/` — Code refactoring

Example: `feature/vector-search-improvements`

### Commit Messages

```
feat(kb): add semantic search caching

- Cache FAISS queries with 1-hour TTL
- Reduces latency by 60% for repeated queries
- Fixes #123

Closes #123
```

### Pull Request Template

```markdown
## Description
Brief summary of changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Testing
- [ ] Added tests
- [ ] All tests pass locally
- [ ] API tested manually

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] PR title follows conventional commits
```

---

## Architecture Decisions

Before making major changes, review:

- **`ARCHITECTURE.md`** — System design
- **Integration points** — How your change affects other components
- **Person responsibilities** — Ensure you're not duplicating work

### Design Review Process

1. Open an issue describing your proposed change
2. Wait for feedback from maintainers
3. Once approved, implement and open PR
4. PR must pass all tests before merge

---

## Performance Considerations

### Before Optimizing

- Measure current performance (use `time` or profiling tools)
- Identify bottleneck with profiling
- Estimate improvement

Example:

```python
import time

start = time.time()
result = kb.retrieve("data breach", top_k=5)
elapsed = time.time() - start
print(f"Retrieval took {elapsed:.3f}s")
```

### After Optimizing

- Benchmark old vs. new
- Document performance improvement
- Ensure no regressions in other areas

---

## Documentation

### Updating Docs

1. Edit relevant `.md` file
2. Test any code examples
3. Preview in markdown viewer
4. Include in PR

### Adding New Endpoints

1. Implement endpoint in routes/
2. Add to `API.md` with:
   - URL and method
   - Request/response schema
   - Example requests (curl, Python, TypeScript)
   - Error cases
3. Swagger documentation auto-generated (run `bash openapi-sync.sh`)

### Adding New SDK Methods

1. Implement method in `sdk-python/client.py` and `sdk-npm/src/client.ts`
2. Add to `SDK_USAGE.md` with examples
3. Update `openapi-sync.sh` output

---

## Dependency Management

### Python

- Pin versions in `requirements.txt`
- Add new dependencies with `pip install package==version`
- Document why dependency is needed

```
# requirements.txt
fastapi==0.104.0    # Web framework
httpx==0.24.0       # HTTP client for SDKs
```

### Node.js

- Use `npm install --save package@version`
- Commit `package-lock.json`
- Document in `package.json` comments

---

## Common Mistakes

❌ **Don't:**
- Commit `.env` files with secrets
- Push to `main` directly (use PR)
- Add `node_modules/` or `__pycache__/` to git
- Make multiple unrelated changes in one PR
- Skip tests

✅ **Do:**
- Use `.env.example` for configuration templates
- Create descriptive branch names
- Write clear commit messages
- Test locally before pushing
- Keep PRs focused and reviewable

---

## Review Process

### What Maintainers Look For

1. **Tests:** All tests passing, new features have tests
2. **Documentation:** Changes documented clearly
3. **Performance:** No regressions, improvements explained
4. **Style:** Code follows project standards
5. **Scope:** Changes are focused and minimal

### Responding to Feedback

- Address all comments
- Push new commits (don't rebase unless asked)
- Re-request review after changes
- Ask for clarification if feedback is unclear

---

## Release Process

### Version Numbers

- Format: `MAJOR.MINOR.PATCH` (e.g., `0.1.0`)
- `MAJOR`: Breaking changes
- `MINOR`: New features
- `PATCH`: Bug fixes

### Creating a Release

1. Update version in:
   - `pyproject.toml` (Python SDK)
   - `package.json` (TypeScript SDK)
   - `CHANGELOG.md`

2. Merge to `main`

3. Tag release:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

4. Create GitHub release with changelog

5. Publish to registries:
   ```bash
   # Python
   cd sdk-python
   pip install build twine
   python -m build
   twine upload dist/*
   
   # TypeScript
   cd sdk-npm
   npm publish
   ```

---

## Getting Help

- **Questions?** Open a discussion on GitHub
- **Found a bug?** Open an issue with reproduction steps
- **Need a feature?** Open an issue and describe use case
- **Need help?** Comment on an issue or PR

---

## Code of Conduct

- Be respectful and inclusive
- Welcome diverse perspectives
- Report inappropriate behavior to maintainers
- Focus on the work, not the person

---

## Recognition

Contributors are recognized in:
- `CHANGELOG.md` per release
- GitHub contributors page
- Project README (major contributors)

Thank you for contributing! 🙏

