"""
Parse locally stored IT Act 2000 PDFs (already downloaded in kb_raw/).

This script:
1. Uses the PDFs you've already downloaded in kb_raw/
2. Extracts text from both PDFs
3. Parses sections using regex
4. Detects struck_down and omitted sections
5. Outputs it_act_2000_parsed.json

Runnable as: python -m api.kb.parse_local_pdfs
"""

import os
import re
import json
import sys
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print("Error: pdfplumber not installed. Run: pip install pdfplumber")
    sys.exit(1)


KB_RAW_DIR = Path(__file__).parent / "kb_raw"
PDF_PATHS = [
    KB_RAW_DIR / "it_act_2000_updated.pdf",
    KB_RAW_DIR / "550681ab908f8afb135b0ad42816a1c9.pdf",
]
JSON_PATH = KB_RAW_DIR / "it_act_2000_parsed.json"


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from PDF page by page."""
    print(f"\n  Extracting from: {Path(pdf_path).name}")
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"    Pages: {total_pages}")

            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text() or ""
                    text_parts.append(page_text)
                except Exception as e:
                    print(f"    ⚠ Error on page {page_num}: {e}")
                    continue

                if page_num % 10 == 0:
                    print(f"    Processed {page_num}/{total_pages}...")

            print(f"    Processed {total_pages}/{total_pages}")

        full_text = "\n".join(text_parts)
        print(f"    ✓ Extracted {len(full_text)} characters")
        return full_text

    except Exception as e:
        print(f"    ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return ""


def skip_table_of_contents(raw_text: str) -> str:
    """Remove TOC and preamble before actual section text."""
    marker = "BE it enacted by Parliament"
    marker_idx = raw_text.find(marker)

    if marker_idx == -1:
        # Fallback: look for first section header
        match = re.search(r"^(\d+[A-Z]{0,2})\.", raw_text, re.MULTILINE)
        if match:
            marker_idx = match.start()
        else:
            return raw_text

    body_text = raw_text[marker_idx:]
    return body_text


def parse_sections(body_text: str) -> list[dict]:
    """Parse section headers and text from statute body."""
    print("  Parsing sections...")

    pattern = r"^(\d{1,3}[A-Z]{0,2})\.\s+(.+?)(?=^\d{1,3}[A-Z]{0,2}\.\s|\Z)"
    matches = re.finditer(pattern, body_text, re.MULTILINE | re.DOTALL)

    sections = []
    for match in matches:
        section_number = match.group(1).strip()
        section_text = match.group(2).strip()

        # Clean up footnote markers
        section_text = re.sub(r"\s+\d+\s*$", "", section_text, flags=re.MULTILINE)
        section_text = re.sub(r"\s+\d+\s+", " ", section_text)
        section_text = re.sub(r"\n\s*\n+", "\n", section_text)
        section_text = re.sub(r"\s+", " ", section_text)

        sections.append({
            "number": section_number,
            "text": section_text,
        })

    print(f"  ✓ Parsed {len(sections)} sections")
    return sections


def tag_statuses(sections: list[dict]) -> list[dict]:
    """Assign status (active, struck_down, omitted) to each section."""
    print("  Tagging statuses...")

    # Known omitted sections
    omitted_sections = [
        "49", "50", "51", "52", "53", "54", "56",  # Chapter X (Repealed)
        "91", "92", "93", "94",  # Not enacted
    ]

    # Known struck_down sections
    struck_down_sections = [
        "66A",  # Shreya Singhal v. Union of India, 2015
    ]

    for section in sections:
        sec_num = section["number"]
        text = section["text"]

        if "[Omitted.]" in text or "Omitted" in text:
            section["status"] = "omitted"
        elif sec_num in omitted_sections:
            section["status"] = "omitted"
        elif sec_num in struck_down_sections:
            section["status"] = "struck_down"
        else:
            section["status"] = "active"

    # Summary
    active = sum(1 for s in sections if s["status"] == "active")
    struck = sum(1 for s in sections if s["status"] == "struck_down")
    omitted = sum(1 for s in sections if s["status"] == "omitted")

    print(f"  ✓ Statuses tagged:")
    print(f"    • Active: {active}")
    print(f"    • Struck down: {struck}")
    print(f"    • Omitted: {omitted}")

    return sections


def save_parsed_json(sections: list[dict], path: str) -> None:
    """Save parsed sections to JSON."""
    print(f"\n  Saving to: {Path(path).name}")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved {len(sections)} sections")


def main():
    """Parse local PDFs and output JSON."""
    print("\n" + "=" * 70)
    print("IT Act, 2000 — Local PDF Parser")
    print("=" * 70)

    all_sections = []

    # Parse each PDF
    print("\n--- EXTRACTING TEXT FROM LOCAL PDFs ---")
    for pdf_path in PDF_PATHS:
        if not pdf_path.exists():
            print(f"\n✗ File not found: {pdf_path}")
            continue

        raw_text = extract_text_from_pdf(str(pdf_path))
        if not raw_text:
            continue

        # Skip TOC
        body_text = skip_table_of_contents(raw_text)

        # Parse sections
        sections = parse_sections(body_text)
        all_sections.extend(sections)

    print(f"\n--- CONSOLIDATING RESULTS ---")
    print(f"Total sections from all PDFs: {len(all_sections)}")

    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_sections = []
    for section in all_sections:
        if section["number"] not in seen:
            seen.add(section["number"])
            unique_sections.append(section)

    print(f"After deduplication: {len(unique_sections)} sections")

    if len(unique_sections) < 50:
        print(f"\n⚠ WARNING: Only {len(unique_sections)} sections parsed.")
        print("  Expected ~85+ sections. PDFs may have parsing issues.")

    # Tag statuses
    print("\n--- TAGGING STATUSES ---")
    unique_sections = tag_statuses(unique_sections)

    # Save JSON
    print("\n--- SAVING JSON ---")
    save_parsed_json(unique_sections, str(JSON_PATH))

    # Summary
    print("\n" + "=" * 70)
    print("PARSING COMPLETE")
    print("=" * 70)
    print(f"\nParsed {len(unique_sections)} sections from local PDFs")
    print(f"Output: {JSON_PATH}")
    print(f"\n⚠ NEXT STEP:")
    print(f"Load into database:")
    print(f"  python -m api.kb.load_parsed_sections")
    print("\n" + "=" * 70 + "\n")

    return len(unique_sections) > 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
