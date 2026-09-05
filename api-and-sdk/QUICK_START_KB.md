# Quick Start: IT Act 2000 Knowledge Base

Fast reference for executing the full KB scraper workflow.

---

## TL;DR - Run These Commands

```bash
# Navigate to api-and-sdk
cd api-and-sdk

# 1. Install dependencies (includes requests, pdfplumber)
pip install -r requirements.txt

# 2. Initialize database schema (if not already done)
python -m api.kb.init_db

# 3. Scrape and parse the IT Act PDF
python -m api.kb.scrape_it_act

# 4. [PAUSE] Manually verify the JSON output (Step 3 in full guide)
#    Key check: Section 66A should have "status": "struck_down"

# 5. Load parsed sections into Postgres
python -m api.kb.load_parsed_sections

# 6. Quick verification
python << 'EOF'
from api.kb.postgres_kb import PostgresKB
kb = PostgresKB()
s66a = kb.lookup_section("66A", "Information Technology Act, 2000")
print(f"✓ Section 66A loaded: {s66a[:80]}...")
EOF
```

---

## What Gets Created

| Path | Size | Purpose | Gitignored? |
|------|------|---------|------------|
| `api/kb/kb_raw/it_act_2000_source.pdf` | ~5 MB | Raw PDF from India Code | ✓ Yes |
| `api/kb/kb_raw/it_act_2000_parsed.json` | ~500 KB | Parsed sections (for review) | ✓ Yes |
| Postgres DB: `statute_sections` table | — | 94 sections from IT Act | — |

---

## Key Facts

- **Sections parsed**: ~94 (including lettered subsections like 43A, 66A)
- **Active sections**: ~85
- **Struck down**: 1 (Section 66A — critical test case)
- **Omitted**: ~8
- **Execution time**: ~15-35 seconds total

---

## Manual Spot-Check (Before Step 5)

After `scrape_it_act` completes, check the JSON:

```bash
# View file
notepad api\kb\kb_raw\it_act_2000_parsed.json

# Look for these sections:
# - "43A" → should have "status": "active"
# - "66" → should have "status": "active"
# - "66A" → should have "status": "struck_down"  ← CRITICAL
# - "69" → should have "status": "active"
# - "79" → should have "status": "active"
```

If Section 66A shows `"status": "active"`, edit the JSON manually before loading:

```json
{
  "number": "66A",
  "text": "...",
  "status": "struck_down"
}
```

---

## Verification After Loading

```bash
python << 'EOF'
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

session = SessionLocal()

# Count by status
from sqlalchemy import func
result = session.query(
    StatuteSection.status, 
    func.count(StatuteSection.id)
).group_by(StatuteSection.status).all()

print("\nSections by status:")
for status, count in result:
    print(f"  {status}: {count}")

# Check Section 66A specifically
s66a = session.query(StatuteSection).filter(
    StatuteSection.section_number == "66A"
).first()
print(f"\nSection 66A: {s66a.status}" if s66a else "\nSection 66A: NOT FOUND")

session.close()
EOF
```

---

## If Something Goes Wrong

| Issue | Fix |
|-------|-----|
| `requests` not found | `pip install requests` |
| `pdfplumber` not found | `pip install pdfplumber` |
| Download fails (timeout) | Re-run `scrape_it_act`, or download PDF manually to `kb_raw/` |
| DATABASE_URL error | Fill in `.env` with your Neon connection string, see `KB_SETUP_GUIDE.md` |
| JSON parsing error | Run `python -m json.tool api/kb/kb_raw/it_act_2000_parsed.json` to validate |
| Section 66A status wrong | Manually edit JSON or run the SQL fix (see full guide, Step 3) |

---

## Next: Use the KB in Your Code

```python
from api.kb.postgres_kb import PostgresKB

kb = PostgresKB()

# Lookup a section by number
text = kb.lookup_section("66", "Information Technology Act, 2000")
print(text)

# Lookup returns None if not found
text = kb.lookup_section("999", "Information Technology Act, 2000")
print(text)  # → None

# retrieve() not yet implemented (lives in vector_kb.py)
try:
    kb.retrieve("hacking", top_k=5)
except NotImplementedError:
    print("Use PostgresKB for exact lookup only; semantic search coming soon")
```

---

## Full Documentation

- **Setup**: See `KB_SETUP_GUIDE.md`
- **Scraper workflow**: See `KB_SCRAPER_WORKFLOW.md`
- **Integration into pipeline**: See `KB_INTEGRATION_GUIDE.md` (coming soon)

---

## URLs

- **Primary PDF**: https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf
- **Fallback PDF**: https://prsindia.org/files/bills_acts/bills_parliament/2021/IT Act, 2000.pdf
