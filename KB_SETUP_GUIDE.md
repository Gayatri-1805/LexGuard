# Knowledge Base Setup Guide

This guide walks you through setting up the IT Act, 2000 knowledge base on Neon (serverless Postgres).

## Overview

The KB layer consists of:
- **db.py**: Connection management and session factory
- **models.py**: SQLAlchemy ORM definitions (StatuteSection, CaseLaw)
- **kb_interface.py**: Abstract base class for KB implementations
- **postgres_kb.py**: Exact-match lookup implementation
- **init_db.py**: Schema creation script
- **ingest_statutes.py**: IT Act section ingestion
- **ingest_case_law.py**: Case law ingestion

## Step 1: Install Dependencies

Navigate to the api-and-sdk directory and install requirements:

```bash
cd api-and-sdk
pip install -r requirements.txt
```

This installs:
- `sqlalchemy>=2.0.0` — ORM framework
- `psycopg2-binary>=2.9.0` — PostgreSQL driver
- `python-dotenv>=1.0.0` — Environment variable management
- `fastapi` and `uvicorn` — API framework (for later integration)

## Step 2: Configure DATABASE_URL

Before proceeding, you must fill in your Neon connection string:

### Obtain your Neon connection string:
1. Go to [https://console.neon.tech](https://console.neon.tech)
2. Create or select your project
3. Copy the connection string (format: `postgresql://user:password@ep-xxx.neon.tech/dbname?sslmode=require`)

### Fill in .env:

Edit `api-and-sdk/.env` and paste your connection string:

```bash
# On Windows (PowerShell)
notepad api-and-sdk\.env

# On Mac/Linux
nano api-and-sdk/.env
```

The file should look like:

```
DATABASE_URL=postgresql://myuser:mypassword@ep-abcd1234.neon.tech/mydb?sslmode=require
```

**Important**: The DATABASE_URL **must** be filled in. If it's empty, the import will fail with:
```
RuntimeError: DATABASE_URL environment variable is missing or empty.
```

### Verify .env is not tracked by git:

Make sure `.env` is in `.gitignore` (it is by default):

```bash
cat .gitignore | grep ".env"
```

Should output: `.env`

---

## Step 3: Create Database Schema

Run the initialization script to create tables on Neon:

```bash
cd api-and-sdk
python -m api.kb.init_db
```

### Expected output:

```
======================================================================
Initializing IT Act, 2000 Knowledge Base on Neon
======================================================================

Connecting to database...
✓ Connection successful

Creating schema...

✓ Database schema created successfully!

Tables created:
  • statute_sections
  • case_law

======================================================================
Next steps:
======================================================================
1. Ingest IT Act sections:
   python -m api.kb.ingest_statutes

2. Ingest case law:
   python -m api.kb.ingest_case_law

======================================================================
```

### Troubleshooting connection errors:

**Error: "psycopg2.OperationalError: connection refused"**
- Check that DATABASE_URL is correct
- Verify your Neon project is active
- Check network connectivity to the Neon endpoint

**Error: "SSL certificate problem"**
- Ensure `?sslmode=require` is in the connection string
- On some systems, you may need to set: `export PGSSLMODE=require`

**Error: "password authentication failed"**
- Double-check the username and password in your connection string

---

## Step 4: Ingest IT Act, 2000 Sections

Populate the statute_sections table with real IT Act sections:

```bash
cd api-and-sdk
python -m api.kb.ingest_statutes
```

### Expected output:

```
======================================================================
Ingesting IT Act, 2000 Statute Sections
======================================================================

Act: Information Technology Act, 2000
Sections: 5

✓ Successfully ingested/updated 5 sections

Database verification:
  • Total sections in DB: 5
  • Active sections: 4
  • Struck down sections: 1

Sections:
  • Section 43A
  • Section 66
  • Section 66A [struck_down]
  • Section 69
  • Section 79

======================================================================
```

#### What was ingested:

- **Section 43A**: Compensation for failure to protect data (active)
- **Section 66**: Computer-related offences / hacking (active)
- **Section 66A**: Offensive messages via communication (struck_down) ← Key test case
- **Section 69**: Power to intercept/monitor/decrypt (active)
- **Section 79**: Safe harbor for intermediaries (active)

**Why Section 66A is marked as "struck_down":**
The Supreme Court of India struck it down in *Shreya Singhal v. Union of India* (2015) as unconstitutional for violating freedom of speech. This is a **critical test case** for the hallucination detector: any claim asserting Section 66A is still valid law should be flagged as contradicted.

---

## Step 5: Ingest Case Law

Populate the case_law table with landmark cases:

```bash
cd api-and-sdk
python -m api.kb.ingest_case_law
```

### Expected output:

```
======================================================================
Ingesting Case Law related to IT Act, 2000
======================================================================

Cases: 1

✓ Successfully ingested/updated 1 cases

Database verification:
  • Total cases in DB: 1

Cases:
  • Shreya Singhal v. Union of India (2015) 5 SCC 1 [related: Section 66A]

======================================================================
```

#### What was ingested:

- **Shreya Singhal v. Union of India, (2015) 5 SCC 1**
  - Struck down Section 66A as unconstitutional
  - Related section: 66A
  - Test case: If a claim says "Section 66A is a valid offense," this case proves it false

---

## Step 6: Verify End-to-End

Query the knowledge base to confirm everything is working:

```python
# Example query (in Python REPL)
from api.kb.postgres_kb import PostgresKB

kb = PostgresKB()

# Test exact lookup
section_text = kb.lookup_section("66A", "Information Technology Act, 2000")
print(f"Found Section 66A: {section_text[:100]}...")

# Test fallback (should raise NotImplementedError)
try:
    kb.retrieve("offensive messages", top_k=5)
except NotImplementedError as e:
    print(f"retrieve() correctly not implemented: {e}")
```

---

## Complete Setup Sequence (One-liner)

For quick setup, run these commands in sequence:

```bash
# 1. Install dependencies
pip install -r api-and-sdk/requirements.txt

# 2. Create schema
python -m api.kb.init_db

# 3. Ingest statutes
python -m api.kb.ingest_statutes

# 4. Ingest case law
python -m api.kb.ingest_case_law
```

---

## Files Reference

| File | Purpose |
|------|---------|
| `db.py` | Database engine, SessionLocal, get_db() dependency |
| `models.py` | SQLAlchemy ORM: StatuteSection, CaseLaw |
| `kb_interface.py` | Abstract KnowledgeBase interface |
| `postgres_kb.py` | PostgresKB implementation (exact lookup only) |
| `init_db.py` | Schema creation script |
| `ingest_statutes.py` | IT Act section data loading |
| `ingest_case_law.py` | Case law data loading |
| `.env` | Your actual Neon connection string (not tracked by git) |
| `.env.example` | Template for .env |
| `requirements.txt` | Python dependencies |

---

## Next Steps

Once the KB is populated:

1. **Person A (Detection Engine)** can implement Stage 2 (Ground) to call `PostgresKB.lookup_section()`
2. **Person B** can integrate `PostgresKB` into FastAPI routes for `/check` endpoint
3. **Person C** can build evaluation harness to test claims against the KB

---

## Troubleshooting

### Import Error: "No module named 'api.kb.db'"

Make sure you're running commands from the `api-and-sdk` directory and have Python path set correctly:

```bash
cd api-and-sdk
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
python -m api.kb.init_db
```

Or run from the root directory:

```bash
python -m api.kb.init_db
```

### Section or Case Not Found After Ingestion

Check that the act_name matches exactly:

```python
from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

session = SessionLocal()
sections = session.query(StatuteSection).all()
for s in sections:
    print(f"{s.act_name} - Section {s.section_number}")
session.close()
```

### merge() Creates Duplicates

The `merge()` operation is keyed on the unique constraint `(act_name, section_number)`. If re-running ingestion, it should upsert (update existing, insert new). If duplicates appear, check that section_number is consistent across runs.

---

## Production Notes

- **SSL Mode**: Always use `sslmode=require` in DATABASE_URL for Neon
- **Connection Pooling**: Neon uses serverless instances; ConnectionPool = None is recommended
- **Credentials**: Never commit `.env` with real credentials; always use .env.example template
- **Rate Limiting**: Neon has rate limits on free tier; batch ingestion if loading large datasets
- **Backups**: Use Neon's built-in backup and branching features

---

## Support

For issues:
1. Check the error message carefully (db.py will print clear guidance on missing DATABASE_URL)
2. Verify DATABASE_URL format and connectivity from your machine
3. Check Neon console for any active alerts or maintenance
4. Review the docstrings in each .py file for additional context
