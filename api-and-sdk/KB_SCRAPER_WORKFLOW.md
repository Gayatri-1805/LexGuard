# IT Act, 2000 Knowledge Base Scraper Workflow

Complete guide for scraping, parsing, and loading the Information Technology Act, 2000 (India) into the Postgres knowledge base.

## Overview

The scraper workflow consists of two main stages:

1. **Scrape & Parse** (`scrape_it_act.py`)
   - Downloads the official PDF from India Code
   - Extracts text using pdfplumber
   - Parses sections via regex
   - Detects struck-down and omitted sections
   - Outputs intermediate JSON for manual review

2. **Load into DB** (`load_parsed_sections.py`)
   - Reads the intermediate JSON
   - Verifies section structure
   - Calls existing `ingest_sections()` function
   - Verifies data in Postgres
   - Reports section counts and status breakdown

---

## Step-by-Step Execution

### Step 1: Install Dependencies

Add the new scraping packages to your environment:

```bash
cd api-and-sdk
pip install -r requirements.txt
```

This installs (among others):
- `requests>=2.31.0` — HTTP downloading
- `pdfplumber>=0.10.0` — PDF text extraction

Verify installation:

```bash
python -c "import requests, pdfplumber; print('✓ Dependencies installed')"
```

---

### Step 2: Run Scraper (Scrape & Parse)

Download the official PDF and parse all sections:

```bash
cd api-and-sdk
python -m api.kb.scrape_it_act
```

### Expected Output:

```
======================================================================
IT Act, 2000 (India) — Scraper & Parser
======================================================================

--- STEP 1: DOWNLOAD ---
Downloading IT Act from: https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf
✓ Downloaded successfully (X.XX MB)

--- STEP 2: EXTRACT TEXT ---
Extracting text from PDF: api-and-sdk/api/kb/kb_raw/it_act_2000_source.pdf
Total pages: 123
  Processed 10/123 pages...
  Processed 20/123 pages...
  ...
  Processed 123/123 pages...
✓ Extracted XXXXXX characters

--- STEP 3: SKIP TABLE OF CONTENTS ---
Skipping table of contents...
✓ Skipped 5432 characters (TOC and preamble)

--- STEP 4: PARSE SECTIONS ---
Parsing sections...
✓ Parsed XX sections

--- STEP 5: EXTRACT FOOTNOTES ---
Extracting footnotes...
✓ Found Y mentions of struck_down/omitted sections

--- STEP 6: TAG STATUSES ---
Tagging section statuses...
✓ Tagged statuses:
  • Active: 85
  • Struck down: 1
  • Omitted: 8

--- STEP 7: SAVE JSON ---
Saving parsed JSON to: api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json
✓ Saved 94 sections to JSON

======================================================================
PARSING COMPLETE
======================================================================

Parsed 94 sections
Raw PDF: api-and-sdk/api/kb/kb_raw/it_act_2000_source.pdf
Parsed JSON: api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json

⚠ NEXT STEPS:
1. Manually spot-check the JSON output, especially sections:
   - 43A (Compensation for data protection)
   - 66 (Computer-related offences)
   - 66A (Offensive messages — should be struck_down)
   - 69 (Interception/monitoring)
   - 79 (Safe harbor for intermediaries)

2. Once verified, run:
   python -m api.kb.load_parsed_sections

======================================================================
```

---

### Step 3: Manual Spot-Check (CRITICAL)

Before loading into the database, manually verify key sections in the JSON output:

#### Option A: View in text editor

```bash
# Windows
notepad api-and-sdk\api\kb\kb_raw\it_act_2000_parsed.json

# Mac/Linux
nano api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json
```

#### Option B: Use Python to extract key sections

```python
import json

with open('api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json', 'r') as f:
    sections = json.load(f)

# Check specific sections
key_sections = ['43A', '66', '66A', '69', '79']
for section in sections:
    if section['number'] in key_sections:
        print(f"\n{'='*70}")
        print(f"Section {section['number']} (Status: {section.get('status', 'active')})")
        print(f"{'='*70}")
        print(section['text'][:300] + "..." if len(section['text']) > 300 else section['text'])
```

#### Verification Checklist

For each key section, verify:

| Section | Should Contain | Expected Status |
|---------|---|---|
| 43A | "compensation", "data", "protect" | active |
| 66 | "hacking", "unauthorized", "computer" | active |
| 66A | "offensive", "messages", "communication" | **struck_down** ← Critical |
| 69 | "intercept", "monitor", "decrypt" | active |
| 79 | "intermediary", "safe harbor", "liable" | active |

**Critical Check**: Section 66A **MUST** have `"status": "struck_down"` (not "active").
This is essential for hallucination detection testing.

#### If Section 66A is marked as "active":

This indicates a parsing issue. Options:

1. **Manual override**: Edit the JSON directly
   ```json
   {
     "number": "66A",
     "text": "...",
     "status": "struck_down"
   }
   ```

2. **Check the PDF text**: Open the raw PDF and search for "66A" to see what pdfplumber extracted

3. **Review regex**: The section parsing regex may have captured it incorrectly

If you proceed with an incorrect status, run this fix after loading:

```python
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

session = SessionLocal()
section_66a = session.query(StatuteSection).filter(
    StatuteSection.section_number == "66A"
).first()
if section_66a:
    section_66a.status = "struck_down"
    session.commit()
    print("✓ Section 66A marked as struck_down")
session.close()
```

---

### Step 4: Load into Postgres

Once verified, load the parsed JSON into the database:

```bash
cd api-and-sdk
python -m api.kb.load_parsed_sections
```

### Expected Output:

```
======================================================================
Loading Parsed IT Act, 2000 Sections into Postgres KB
======================================================================

Loading sections from: api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json
✓ Loaded 94 sections from JSON

Verifying section structure...
✓ All 94 sections have required fields

--- INGESTING INTO POSTGRES ---

✓ Successfully ingested/updated 94 sections

--- DATABASE VERIFICATION ---

Database counts:
  • Total sections: 94
  • Active: 85
  • Struck down: 1
  • Omitted: 8

✓ Section 66A found:
  • Status: struck_down
  • ✓ Correctly marked as struck_down

Key sections in database:
  • Section 43A: ✓
  • Section 66: ✓
  • Section 66A [struck_down]: ✓
  • Section 69: ✓
  • Section 79: ✓

======================================================================
LOADING COMPLETE
======================================================================

✓ Successfully loaded 94 sections into Postgres

======================================================================
```

---

### Step 5: Verify in Database

Run a quick query to confirm everything landed correctly:

#### Option A: Python verification script

```python
from api.kb.postgres_kb import PostgresKB

kb = PostgresKB()

# Test exact lookup
section_66_text = kb.lookup_section("66", "Information Technology Act, 2000")
print(f"Section 66 text: {section_66_text[:150]}...\n")

section_66a_text = kb.lookup_section("66A", "Information Technology Act, 2000")
print(f"Section 66A text: {section_66a_text[:150]}...\n")

# Test non-existent section
section_999 = kb.lookup_section("999", "Information Technology Act, 2000")
print(f"Section 999 (should be None): {section_999}\n")

# Test retrieve (should raise NotImplementedError)
try:
    kb.retrieve("hacking", top_k=5)
except NotImplementedError as e:
    print(f"retrieve() correctly not implemented:\n  {e}")
```

#### Option B: Direct SQL query (if you have psql access)

```sql
-- Count sections by status
SELECT status, COUNT(*) as count
FROM statute_sections
WHERE act_name = 'Information Technology Act, 2000'
GROUP BY status
ORDER BY status;

-- Verify Section 66A is struck_down
SELECT section_number, status, section_text
FROM statute_sections
WHERE act_name = 'Information Technology Act, 2000'
  AND section_number = '66A';

-- List all active sections
SELECT section_number
FROM statute_sections
WHERE act_name = 'Information Technology Act, 2000'
  AND status = 'active'
ORDER BY section_number;
```

---

## Complete One-Liner Workflow

For quick setup, run these commands in sequence:

```bash
# 1. Install dependencies
cd api-and-sdk && pip install -r requirements.txt

# 2. Scrape and parse
python -m api.kb.scrape_it_act

# 3. (Manually verify JSON) — see Step 3 above

# 4. Load into database
python -m api.kb.load_parsed_sections

# 5. Verify in Python
python << 'EOF'
from api.kb.postgres_kb import PostgresKB
kb = PostgresKB()
print("✓ Section 66:", kb.lookup_section("66", "Information Technology Act, 2000")[:50])
print("✓ Section 66A (struck_down):", kb.lookup_section("66A", "Information Technology Act, 2000")[:50])
EOF
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `scrape_it_act.py` | Download PDF, extract text, parse sections, detect status |
| `load_parsed_sections.py` | Load JSON into Postgres via ingest_sections() |
| `kb_raw/it_act_2000_source.pdf` | Raw PDF (gitignored) |
| `kb_raw/it_act_2000_parsed.json` | Intermediate JSON for review (gitignored) |
| `requirements.txt` | Dependencies (requests, pdfplumber, etc.) |

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pdfplumber'"

```bash
pip install pdfplumber requests
```

### Error: "Connection refused" / "SSL certificate problem"

You haven't run `init_db.py` yet or DATABASE_URL isn't set. See KB_SETUP_GUIDE.md:

```bash
# First, ensure Postgres is initialized
python -m api.kb.init_db

# Then verify DATABASE_URL
cat .env | grep DATABASE_URL
```

### Error: "JSON decode error" in load_parsed_sections.py

The JSON may be malformed. Validate:

```bash
python -m json.tool api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json | head -20
```

### Section 66A is marked as "active" (not "struck_down")

This is a **critical issue** for hallucination detection testing. See Step 3 (Manual Spot-Check) for recovery.

### Sections are cut off or missing

The PDF extraction may have failed. Rerun `scrape_it_act` and check for warnings about section count < 85:

```bash
python -m api.kb.scrape_it_act 2>&1 | grep -i "warning\|error"
```

### PDF download times out

The URLs may be temporarily unavailable. Try again, or manually download from:
- Primary: https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf
- Fallback: https://prsindia.org/files/bills_acts/bills_parliament/2021/IT Act, 2000.pdf

Then place the PDF at `api-and-sdk/api/kb/kb_raw/it_act_2000_source.pdf` and run `load_parsed_sections.py` directly.

---

## Next Steps

Once the KB is fully loaded:

1. **Person A (Detection Engine)** can now test Stage 2 (Ground) with real statute text
2. **Person B** can integrate `PostgresKB` into the `/check` API route
3. **Person C** can build evaluation test cases (e.g., claiming Section 66A is still valid → should be flagged as hallucination)

---

## Performance Notes

- **PDF download**: ~1-5 seconds (depending on network)
- **Text extraction**: ~10-20 seconds (pdfplumber processes ~123 pages)
- **Section parsing**: ~1-2 seconds (regex on full text)
- **DB insertion**: ~3-5 seconds (94 sections via merge)
- **Total time**: ~15-35 seconds end-to-end

---

## Important Caveats

⚠️ **PDF text extraction is lossy**: Multi-column layouts, footnotes, and page breaks can cause text misalignment.
   - Always spot-check the parsed JSON before loading.
   - The 5 key sections (43A, 66, 66A, 69, 79) are your canary; if they look good, the rest likely are too.

⚠️ **Regex parsing is approximate**: The section header regex handles most cases but may fail on unusual formatting.
   - Expected to parse ~85-94 sections; if << 85, manual review is needed.

⚠️ **Status tagging relies on hardcoded overrides**: If the PDF format changes, the hardcoded struck_down/omitted lists may become inaccurate.
   - Section 66A is hardcoded as "struck_down" (Shreya Singhal v. Union of India, 2015).
   - Sections 91-94 are hardcoded as "omitted" (never enacted).

---

## Support & Debugging

Enable detailed logging during scraping:

```python
# In scrape_it_act.py, change:
engine = create_engine(DATABASE_URL, echo=True)  # Show all SQL

# Run:
python -m api.kb.scrape_it_act 2>&1 | tee scrape_debug.log
```

For PDF extraction issues, test with a simpler document first:

```python
import pdfplumber
with pdfplumber.open('api-and-sdk/api/kb/kb_raw/it_act_2000_source.pdf') as pdf:
    print(f"Total pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages[:3]):
        print(f"\n--- Page {i+1} ---")
        print(page.extract_text()[:200])
```
