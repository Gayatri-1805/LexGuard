#!/usr/bin/env python
"""Check what Section 66 actually contains in the KB"""

import sys
from pathlib import Path

_API_SDK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_API_SDK_ROOT))

from dotenv import load_dotenv
load_dotenv()

from api.kb.db import SessionLocal
from api.kb.models import StatuteSection

session = SessionLocal()

# Find Section 66
section_66 = session.query(StatuteSection).filter(
    StatuteSection.section_number == '66'
).first()

if section_66:
    print(f"✅ Found Section 66 in KB!\n")
    print(f"Act: {section_66.act_name}")
    print(f"Section: {section_66.section_number}")
    print(f"Status: {section_66.status}")
    print(f"\nText (first 500 chars):")
    print(section_66.section_text[:500])
    print(f"\n... (total length: {len(section_66.section_text)} chars)")
else:
    print("❌ Section 66 NOT found in KB!")

# Also check for Section 66A
section_66a = session.query(StatuteSection).filter(
    StatuteSection.section_number == '66A'
).first()

if section_66a:
    print(f"\n\n✅ Section 66A exists:")
    print(f"Text (first 300 chars):")
    print(section_66a.section_text[:300])

# Check what KB search would return
print("\n\n🔍 Testing vector search for 'Section 66'...")
from api.kb.vector_kb import VectorRetriever

retriever = VectorRetriever()
results = retriever.retrieve_with_metadata("Section 66 cyber terrorism computer", top_k=5)

print(f"\nTop 5 results:")
for i, result in enumerate(results, 1):
    print(f"\n{i}. Score: {result['score']:.4f}")
    print(f"   Source: {result.get('source_type', 'unknown')} - {result.get('ref_id', 'unknown')}")
    if 'section_number' in result:
        print(f"   Section: {result['section_number']}")
    print(f"   Text: {result['text'][:150]}...")

session.close()
