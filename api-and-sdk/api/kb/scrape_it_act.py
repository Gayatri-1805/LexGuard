"""
Scraper and parser for the Information Technology Act, 2000 (India).

IMPORTANT CAVEATS:
- This script extracts sections from the official India Code PDF:
  https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf
- PDF text extraction can misorder text in multi-column layouts or merge footnotes into body paragraphs.
- The parsed JSON MUST be manually spot-checked against core demo sections (43A, 66, 66A, 69, 79)
  before running load_parsed_sections.py.
- If footnote extraction proves unreliable, a hardcoded status override dict can be used as fallback
  for known exceptions (66A → struck_down, omitted sections).

Outputs:
  - Raw PDF: api-and-sdk/api/kb/kb_raw/it_act_2000_source.pdf
  - Parsed JSON: api-and-sdk/api/kb/kb_raw/it_act_2000_parsed.json

Runnable as: python -m api.kb.scrape_it_act
"""

import os
import re
import json
import sys
from pathlib import Path

try:
    import requests
    import pdfplumber
except ImportError:
    print("Error: Missing required packages. Install with:")
    print("  pip install requests pdfplumber")
    sys.exit(1)


# Primary and fallback URLs
PRIMARY_URL = "https://www.indiacode.nic.in/bitstream/123456789/13116/1/it_act_2000_updated.pdf"
FALLBACK_URL = "https://prsindia.org/files/bills_acts/bills_parliament/2021/IT Act, 2000.pdf"

# Storage paths
KB_RAW_DIR = Path(__file__).parent / "kb_raw"
PDF_PATH = KB_RAW_DIR / "it_act_2000_source.pdf"
JSON_PATH = KB_RAW_DIR / "it_act_2000_parsed.json"


def ensure_kb_raw_dir():
    """Create kb_raw directory if it doesn't exist."""
    KB_RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_act_pdf(url: str, save_path: str) -> bool:
    """
    Download the IT Act PDF from the given URL.

    Args:
        url: URL to download from
        save_path: Path where PDF will be saved

    Returns:
        True if successful, False otherwise
    """
    print(f"\nDownloading IT Act from: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        with open(save_path, "wb") as f:
            f.write(response.content)

        size_mb = os.path.getsize(save_path) / (1024 * 1024)
        print(f"✓ Downloaded successfully ({size_mb:.2f} MB)")
        return True

    except requests.exceptions.RequestException as e:
        print(f"✗ Download failed: {e}")
        return False


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract raw text from PDF page by page, concatenated in reading order.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Concatenated text from all pages
    """
    print(f"\nExtracting text from PDF: {pdf_path}")
    try:
        text_parts = []
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Total pages: {total_pages}")

            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                text_parts.append(page_text)

                if page_num % 10 == 0 or page_num == total_pages:
                    print(f"  Processed {page_num}/{total_pages} pages...")

        full_text = "\n".join(text_parts)
        print(f"✓ Extracted {len(full_text)} characters")
        return full_text

    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        raise


def skip_table_of_contents(raw_text: str) -> str:
    """
    Remove the table of contents and preamble before the actual section text.

    The PDF begins with an "ARRANGEMENT OF SECTIONS" TOC before "BE it enacted by Parliament..."
    This function strips everything before that marker.

    Args:
        raw_text: Raw extracted text

    Returns:
        Text starting from the enactment clause
    """
    print("\nSkipping table of contents...")

    # Look for the enactment clause as the starting point
    marker = "BE it enacted by Parliament"
    marker_idx = raw_text.find(marker)

    if marker_idx == -1:
        # Fallback: look for first section header
        match = re.search(r"^(\d+[A-Z]{0,2})\.", raw_text, re.MULTILINE)
        if match:
            marker_idx = match.start()
        else:
            print("⚠ Could not find enactment clause or section headers; using full text")
            return raw_text

    body_text = raw_text[marker_idx:]
    skipped_chars = marker_idx
    print(f"✓ Skipped {skipped_chars} characters (TOC and preamble)")
    return body_text


def parse_sections(body_text: str) -> list[dict]:
    """
    Parse section headers and text from the statute body.

    Regex matches Indian statute section headers like "43A.", "66.", "69B.", etc.,
    including lettered sub-sections. Handles multi-line section text.

    Args:
        body_text: Text starting from enactment clause

    Returns:
        List of dicts with keys: number, text
    """
    print("\nParsing sections...")

    # Regex to match section headers: "123A." or "66." followed by section title and text
    # Matches section number (1-3 digits, optional letters), period, and captures until next section or end
    pattern = r"^(\d{1,3}[A-Z]{0,2})\.\s+(.+?)(?=^\d{1,3}[A-Z]{0,2}\.\s|\Z)"

    matches = re.finditer(pattern, body_text, re.MULTILINE | re.DOTALL)

    sections = []
    for match in matches:
        section_number = match.group(1).strip()
        section_text = match.group(2).strip()

        # Clean up footnote markers (superscript-style numbers at end of sentences)
        # But preserve the text; we'll capture footnotes separately
        section_text = re.sub(r"\s+\d+\s*$", "", section_text, flags=re.MULTILINE)
        section_text = re.sub(r"\s+\d+\s+", " ", section_text)

        # Remove excessive whitespace
        section_text = re.sub(r"\n\s*\n+", "\n", section_text)
        section_text = re.sub(r"\s+", " ", section_text)

        sections.append({
            "number": section_number,
            "text": section_text,
        })

    print(f"✓ Parsed {len(sections)} sections")
    return sections


def extract_footnotes(raw_text: str) -> dict[str, str]:
    """
    Extract footnotes from the PDF text.

    Footnotes in this PDF appear at the bottom of pages and contain legal facts
    (e.g., that Section 66A was struck down). We extract them and map to sections.

    Args:
        raw_text: Raw extracted text containing footnotes

    Returns:
        Dict mapping section references to footnote text
    """
    print("\nExtracting footnotes...")

    footnotes = {}

    # Look for footnote patterns: small numbered markers followed by text
    # Typical pattern: "1" or "2" at start of line, followed by note text
    footnote_pattern = r"^(\d+)\s+(.+?)(?=^\d+\s+|\Z)"

    # This is a simplified extraction; may need tuning based on actual PDF format
    # Look for mentions of struck down, amended, omitted
    struck_down_mentions = re.findall(
        r"(Section\s+\d+[A-Z]{0,2}|66A).*?(struck down|struck off|deleted|omitted)",
        raw_text,
        re.IGNORECASE
    )

    if struck_down_mentions:
        print(f"✓ Found {len(struck_down_mentions)} mentions of struck_down/omitted sections")
        for mention in struck_down_mentions:
            footnotes[mention[0]] = f"Status mentioned in document: {mention[1]}"

    if not footnotes:
        print("⚠ No footnotes extracted; will rely on section body or hardcoded overrides")

    return footnotes


def tag_statuses(sections: list[dict], footnotes: dict) -> list[dict]:
    """
    Assign status (active, struck_down, omitted, amended) to each section.

    Uses footnotes and section body content to derive status.

    Args:
        sections: List of parsed sections
        footnotes: Dict of footnotes

    Returns:
        Sections with 'status' field added
    """
    print("\nTagging section statuses...")

    # Hardcoded known overrides for sections that are definitely omitted
    # per the actual IT Act, 2000 (sections not in statute)
    omitted_sections = [
        "49", "50", "51", "52", "53", "54", "56",  # Chapter X sections (Repealed)
        "91", "92", "93", "94",  # Not enacted sections
    ]

    # Hardcoded known struck_down sections (from Supreme Court judgments)
    struck_down_sections = [
        "66A",  # Shreya Singhal v. Union of India, 2015
    ]

    for section in sections:
        sec_num = section["number"]
        text = section["text"]

        # Check if section is marked as omitted in the text itself
        if "[Omitted.]" in text or "Omitted" in text:
            section["status"] = "omitted"
        # Check hardcoded omitted list
        elif sec_num in omitted_sections:
            section["status"] = "omitted"
        # Check hardcoded struck_down list
        elif sec_num in struck_down_sections:
            section["status"] = "struck_down"
        # Check footnotes
        elif any(sec_num in key for key in footnotes.keys()):
            footnote_text = " ".join(footnotes.values())
            if "struck" in footnote_text.lower() or "deleted" in footnote_text.lower():
                section["status"] = "struck_down"
            elif "omitted" in footnote_text.lower():
                section["status"] = "omitted"
            else:
                section["status"] = "active"
        # Default
        else:
            section["status"] = "active"

    # Summary
    active_count = sum(1 for s in sections if s["status"] == "active")
    struck_down_count = sum(1 for s in sections if s["status"] == "struck_down")
    omitted_count = sum(1 for s in sections if s["status"] == "omitted")

    print(f"✓ Tagged statuses:")
    print(f"  • Active: {active_count}")
    print(f"  • Struck down: {struck_down_count}")
    print(f"  • Omitted: {omitted_count}")

    return sections


def save_parsed_json(sections: list[dict], path: str) -> None:
    """
    Save parsed sections to JSON for human review.

    Args:
        sections: List of parsed sections with status
        path: Path where JSON will be saved
    """
    print(f"\nSaving parsed JSON to: {path}")

    os.makedirs(os.path.dirname(path), exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(sections)} sections to JSON")


def main():
    """Run the full scrape and parse pipeline."""
    print("\n" + "=" * 70)
    print("IT Act, 2000 (India) — Scraper & Parser")
    print("=" * 70)

    ensure_kb_raw_dir()

    # Step 1: Download PDF
    print("\n--- STEP 1: DOWNLOAD ---")
    pdf_downloaded = download_act_pdf(PRIMARY_URL, str(PDF_PATH))

    if not pdf_downloaded:
        print("\nTrying fallback URL...")
        pdf_downloaded = download_act_pdf(FALLBACK_URL, str(PDF_PATH))

    if not pdf_downloaded:
        print("✗ Failed to download from both URLs")
        return False

    # Step 2: Extract text
    print("\n--- STEP 2: EXTRACT TEXT ---")
    try:
        raw_text = extract_text_from_pdf(str(PDF_PATH))
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        return False

    # Step 3: Skip TOC
    print("\n--- STEP 3: SKIP TABLE OF CONTENTS ---")
    body_text = skip_table_of_contents(raw_text)

    # Step 4: Parse sections
    print("\n--- STEP 4: PARSE SECTIONS ---")
    sections = parse_sections(body_text)

    if len(sections) < 85:
        print(f"\n⚠ WARNING: Only parsed {len(sections)} sections.")
        print("  The IT Act has ~94 numbered sections. The regex may have missed some.")
        print("  Please manually spot-check the JSON output.")

    # Step 5: Extract footnotes
    print("\n--- STEP 5: EXTRACT FOOTNOTES ---")
    footnotes = extract_footnotes(raw_text)

    # Step 6: Tag statuses
    print("\n--- STEP 6: TAG STATUSES ---")
    sections = tag_statuses(sections, footnotes)

    # Step 7: Save JSON
    print("\n--- STEP 7: SAVE JSON ---")
    save_parsed_json(sections, str(JSON_PATH))

    # Summary
    print("\n" + "=" * 70)
    print("PARSING COMPLETE")
    print("=" * 70)
    print(f"\nParsed {len(sections)} sections")
    print(f"Raw PDF: {PDF_PATH}")
    print(f"Parsed JSON: {JSON_PATH}")
    print("\n⚠ NEXT STEPS:")
    print("1. Manually spot-check the JSON output, especially sections:")
    print("   - 43A (Compensation for data protection)")
    print("   - 66 (Computer-related offences)")
    print("   - 66A (Offensive messages — should be struck_down)")
    print("   - 69 (Interception/monitoring)")
    print("   - 79 (Safe harbor for intermediaries)")
    print("\n2. Once verified, run:")
    print("   python -m api.kb.load_parsed_sections")
    print("\n" + "=" * 70 + "\n")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
