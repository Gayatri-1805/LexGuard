"""
Generate Week 3 Project Progress Diary - Pages 26-27 (Odd Semester)
Exact replica of TCET Major Project I Weekly Logbook template.

Run:  python generate_week3_progress_diary.py
Output: LexGuard_Week3_Diary_Pages26_27.docx
"""

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


# ── XML helpers ────────────────────────────────────────────────────────────────

def set_cell_bg(cell, hex_color):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)


def set_table_borders(table, color="000000", sz="6", val="single"):
    tbl = table._tbl
    tblPr = tbl.find(qn("w:tblPr"))
    if tblPr is None:
        tblPr = OxmlElement("w:tblPr")
        tbl.insert(0, tblPr)
    # remove existing borders element if any
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    tblBorders = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = OxmlElement(f"w:{side}")
        tag.set(qn("w:val"), val)
        tag.set(qn("w:sz"), sz)
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), color)
        tblBorders.append(tag)
    tblPr.append(tblBorders)


def set_cell_width(cell, width_twips):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement("w:tcW")
    tcW.set(qn("w:w"), str(width_twips))
    tcW.set(qn("w:type"), "dxa")
    tcPr.append(tcW)


def merge_row_cells(row, start, end):
    """Merge cells in a row from index start to end (inclusive)."""
    row.cells[start].merge(row.cells[end])


def cell_para(cell, text, bold=False, size=9, color=(0, 0, 0),
              align=WD_ALIGN_PARAGRAPH.LEFT, italic=False,
              space_before=2, space_after=2):
    # Clear existing paragraphs
    for p in cell.paragraphs:
        p.clear()
    p = cell.paragraphs[0]
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    if text:
        r = p.add_run(text)
        r.bold = bold
        r.italic = italic
        r.font.name = "Times New Roman"
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(*color)
    return p


def add_centered_para(doc, text, bold=False, size=11, color=(0, 0, 0),
                       space_before=2, space_after=2, underline=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    r.bold = bold
    r.underline = underline
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(*color)
    return p


def add_para(doc, text, bold=False, size=10, color=(0, 0, 0),
             align=WD_ALIGN_PARAGRAPH.LEFT,
             space_before=1, space_after=1):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    r.bold = bold
    r.font.name = "Times New Roman"
    r.font.size = Pt(size)
    r.font.color.rgb = RGBColor(*color)
    return p


# ── Content for the 5 tracker rows ────────────────────────────────────────────
# Columns: Project Component | Planned Work | Previous Status + Gap | Action Taken | Evidence | Current Status & Next Target

TRACKER_ROWS = [
    {
        "component": "Literature Survey &\nResearch Gap",
        "planned":   "Review existing legal NLP and hallucination-detection papers. Identify research gap in Indian statutory context (IT Act 2000).",
        "prev_status": "Week 1-2: 8 papers surveyed (FEVER, HaluEval, LegalBench). Gap: No system targets Indian cyber-law statutes specifically.",
        "action":    "Completed literature matrix. Finalized 12 key references. Confirmed novelty: LexGuard is the first RAG-based hallucination detector grounded in the IT Act 2000.",
        "evidence":  "Literature matrix spreadsheet. 12 annotated references. Research gap statement drafted in report Ch. 2.",
        "current":   "Complete. Next: Incorporate guide feedback on gap statement. Update related work section in report draft.",
    },
    {
        "component": "Problem Definition,\nObjectives &\nScope",
        "planned":   "Finalize problem statement, 5 measurable objectives, and project scope (IT Act 2000, 3-class verdict: SAFE / FLAGGED / ABSTAIN).",
        "prev_status": "Week 2: Draft problem statement written. Objectives not yet quantified. Scope boundary undefined.",
        "action":    "Problem statement finalized: 'Detect and score factual hallucinations in LLM-generated legal text using multi-stage RAG pipeline grounded in IT Act 2000.' 5 objectives set with measurable KPIs (Accuracy >= 80%, latency < 2s).",
        "evidence":  "Finalized problem statement. Objectives table with KPIs in project report Ch. 1.",
        "current":   "Complete. Next: Begin Ch. 3 methodology writeup aligning objectives to pipeline stages.",
    },
    {
        "component": "Architecture /\nAlgorithm /\nMethodology",
        "planned":   "Design multi-stage pipeline: Stage 0 (Claim Decomposition) -> Stage 2 (KB Retrieval) -> Stage 2.5 (Entailment) -> Stage 4 (Trust Index). Finalize tech stack.",
        "prev_status": "Week 2: High-level block diagram drafted. Tech stack not finalized. FAISS vs Qdrant decision pending.",
        "action":    "Full pipeline architecture finalized. Selected: FAISS Flat-L2 (127 chunks, sub-50ms), sentence-transformers/all-MiniLM-L6-v2, GPT-4o-mini as judge, FastAPI backend, Neon PostgreSQL. System flow diagram drawn.",
        "evidence":  "Architecture diagram (Fig 4.1). Tech stack decision table. ARCHITECTURE.md committed to GitHub.",
        "current":   "Complete. Next: Implement Stage 0 (Claim Decomposition) and Stage 2.5 (LLM-as-a-Judge) in Week 4.",
    },
    {
        "component": "Implementation,\nDataset, Tools &\nTesting",
        "planned":   "Build Knowledge Base: parse 115 IT Act sections + 12 case law entries. Generate FAISS index. Scaffold FastAPI /api/check endpoint.",
        "prev_status": "Week 2: Python environment set up. No KB or index built. FastAPI project scaffolded (empty routes).",
        "action":    "IT Act 2000 KB fully parsed (115 sections). 12 landmark judgements added (Shreya Singhal, CBI v. Arif Azim, etc.). FAISS index built: 384-dim embeddings, avg retrieval latency 40ms. /api/check endpoint functional with Pydantic v2 models. 8 unit tests passed.",
        "evidence":  "it_act_sections.json (115 entries). case_law.json (12 entries). FAISS index file. test_api.py (8/8 tests pass). GitHub commit log.",
        "current":   "KB & API complete. Next: Implement claim decomposition + trust index aggregation pipeline in Week 4.",
    },
    {
        "component": "Results,\nDocumentation,\nPresentation &\nTeamwork",
        "planned":   "Set up GitHub repository with branch protection. Divide implementation tasks across 3 team members. Update project report Ch. 1-2.",
        "prev_status": "Week 2: GitHub repo created. Task division informal. Report Ch. 1 draft written.",
        "action":    "GitHub repo structured with 3 sub-folders (detection-engine, api-and-sdk, dashboard-and-eval). Branch protection enabled. shared/schemas.py interface contract agreed. Report Ch. 1 & 2 updated. Team sync meeting held; next meeting scheduled for Week 4.",
        "evidence":  "GitHub repo (branch graph). schemas.py commit. Updated report Ch. 1-2 (PDF). Meeting notes.",
        "current":   "On track. Next: Complete Ch. 3 (Methodology) and begin Ch. 4 (Implementation) writeup.",
    },
]


# ── Main builder ───────────────────────────────────────────────────────────────

def build(output="LexGuard_Week3_Diary_Pages26_27.docx"):
    doc = Document()

    # Narrow margins to fit table
    for sec in doc.sections:
        sec.top_margin    = Cm(1.5)
        sec.bottom_margin = Cm(1.5)
        sec.left_margin   = Cm(1.8)
        sec.right_margin  = Cm(1.5)

    # ══════════════════════════════════════════════════════════════════
    # PAGE 26 — Weekly Logbook
    # ══════════════════════════════════════════════════════════════════

    # ── HEADER ────────────────────────────────────────────────────────
    add_centered_para(doc, "MAJOR PROJECT I", bold=True, size=13,
                      space_before=0, space_after=0)
    add_centered_para(doc, "A.Y 2026-2027  ( odd semester)", bold=False, size=11,
                      space_before=0, space_after=0)
    add_centered_para(doc, "WEEKLY PROJECT LOGBOOK", bold=True, size=12,
                      underline=True, space_before=0, space_after=4)

    # ── Week No / Reporting Date row (single-row 2-col table) ─────────
    wk_tbl = doc.add_table(rows=1, cols=2)
    wk_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(wk_tbl, sz="6")
    cell_para(wk_tbl.rows[0].cells[0], "Week No.: 03",
              bold=True, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_para(wk_tbl.rows[0].cells[1], "Reporting Date: __________",
              bold=False, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

    # ── Project Info Table (3-col, 2-row) ─────────────────────────────
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    info_tbl = doc.add_table(rows=2, cols=3)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(info_tbl, sz="6")

    # Row 0: Project Title | Group No. | Guide Name
    info_tbl.rows[0].cells[0].paragraphs[0].clear()
    p0 = info_tbl.rows[0].cells[0].paragraphs[0]
    p0.paragraph_format.space_before = Pt(2)
    p0.paragraph_format.space_after = Pt(8)
    rb = p0.add_run("Project Title: ")
    rb.bold = True; rb.font.name = "Times New Roman"; rb.font.size = Pt(9)
    rt = p0.add_run("LexGuard: A Multi-Stage Pipeline for Legal LLM Hallucination Detection")
    rt.font.name = "Times New Roman"; rt.font.size = Pt(9)

    cell_para(info_tbl.rows[0].cells[1],
              "Group No.: ____", bold=False, size=9)
    cell_para(info_tbl.rows[0].cells[2],
              "Guide Name: ____________________", bold=False, size=9)

    # Row 1: Student Names & Roll Nos | Project Domain | Previous Cumulative Progress
    p1 = info_tbl.rows[1].cells[0].paragraphs[0]
    p1.clear()
    p1.paragraph_format.space_before = Pt(2)
    p1.paragraph_format.space_after = Pt(8)
    rb1 = p1.add_run("Student Names & Roll Nos.: ")
    rb1.bold = True; rb1.font.name = "Times New Roman"; rb1.font.size = Pt(9)
    rt1 = p1.add_run("Niyati Atugade (04), Gayatri Warty (10), Mansi More (26)")
    rt1.font.name = "Times New Roman"; rt1.font.size = Pt(9)

    cell_para(info_tbl.rows[1].cells[1],
              "Project Domain: AI / NLP / Legal Tech", bold=False, size=9)
    cell_para(info_tbl.rows[1].cells[2],
              "Previous Cumulative Progress: ____  %", bold=False, size=9)

    # ── WEEKLY CONTINUOUS IMPROVEMENT TRACKER ─────────────────────────
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    add_centered_para(doc, "WEEKLY CONTINUOUS IMPROVEMENT TRACKER",
                      bold=True, size=10, space_before=2, space_after=2)

    # Main tracker table: 6 columns, header + 5 component rows
    # Col widths (approx, in twips: 1 inch = 1440):
    # Component(~1.5"), Planned(~1.4"), Prev Status(~1.4"), Action(~1.4"), Evidence(~1.4"), Current Status(~1.4")
    num_cols = 6
    tracker = doc.add_table(rows=1 + len(TRACKER_ROWS), cols=num_cols)
    tracker.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(tracker, sz="6")

    # Column widths in twips
    col_widths = [1500, 1300, 1350, 1350, 1200, 1300]
    for row in tracker.rows:
        for i, cell in enumerate(row.cells):
            set_cell_width(cell, col_widths[i])

    # Header row
    HEADERS = [
        "Project Component /\nParameter",
        "Planned Work /\nWeekly Target",
        "Previous Status +\nGuide Feedback / Gap",
        "Action Taken /\nWork Completed",
        "Evidence /\nOutput Produced",
        "Current Status,\nImprovement &\nNext Target",
    ]
    hdr_row = tracker.rows[0]
    for i, h in enumerate(HEADERS):
        set_cell_bg(hdr_row.cells[i], "D9D9D9")
        cell_para(hdr_row.cells[i], h, bold=True, size=8,
                  align=WD_ALIGN_PARAGRAPH.CENTER,
                  space_before=3, space_after=3)

    # Data rows
    for ri, row_data in enumerate(TRACKER_ROWS):
        tr = tracker.rows[ri + 1]
        vals = [
            row_data["component"],
            row_data["planned"],
            row_data["prev_status"],
            row_data["action"],
            row_data["evidence"],
            row_data["current"],
        ]
        for ci, val in enumerate(vals):
            bold = (ci == 0)
            align = WD_ALIGN_PARAGRAPH.CENTER if ci == 0 else WD_ALIGN_PARAGRAPH.LEFT
            cell_para(tr.cells[ci], val, bold=bold, size=7.5,
                      align=align, space_before=3, space_after=3)

    # ── PROGRESS, GUIDE ASSESSMENT AND AUTHENTICATION ─────────────────
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    add_centered_para(doc, "PROGRESS, GUIDE ASSESSMENT AND AUTHENTICATION",
                      bold=True, size=10, space_before=2, space_after=2)

    # Assessment table: complex layout — replicate with a 4-col table
    # Row 1: Current Progress ____% | Weekly Improvement ____% | Improvement Status | Work Status
    # Row 2: Guide Rating (1-4) ____ | Response to Feedback (1-4) ____ | Next Week Target | Target Date
    # Row 3: Student Signature | Guide Remark | Guide Signature & Date | Evidence Verified Yes/No

    assess = doc.add_table(rows=3, cols=4)
    assess.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(assess, sz="6")
    assess_widths = [2150, 2150, 2150, 1550]
    for row in assess.rows:
        for i, cell in enumerate(row.cells):
            set_cell_width(cell, assess_widths[i])

    # Row 0
    cell_para(assess.rows[0].cells[0],
              "Current Progress:  ____  %",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[0].cells[1],
              "Weekly Improvement:  ____  %",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[0].cells[2],
              "Improvement Status:\nMinor / Moderate / Significant",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[0].cells[3],
              "Work Status:\nOn Track / Delayed",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)

    # Row 1
    cell_para(assess.rows[1].cells[0],
              "Guide Rating (1-4):  ____",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[1].cells[1],
              "Response to Feedback (1-4):  ____",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[1].cells[2],
              "Next Week Target:\nComplete pipeline Stages 0, 2.5, 4",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[1].cells[3],
              "Target Date:\n10 Oct 2026",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)

    # Row 2 — signatures
    cell_para(assess.rows[2].cells[0],
              "Student Signature:\n\n\n________________________",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[2].cells[1],
              "Guide Remark:\n\n\n________________________",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[2].cells[2],
              "Guide Signature & Date:\n\n\n________________________",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)
    cell_para(assess.rows[2].cells[3],
              "Evidence Verified:\nYes / No",
              bold=False, size=9, align=WD_ALIGN_PARAGRAPH.CENTER,
              space_before=6, space_after=6)

    # ── PAGE FOOTER ───────────────────────────────────────────────────
    doc.add_paragraph().paragraph_format.space_after = Pt(4)
    add_para(doc,
             "Department of Artificial Intelligence & Machine Learning, TCET  |  Major Project I Weekly Logbook",
             bold=False, size=8, color=(80, 80, 80),
             align=WD_ALIGN_PARAGRAPH.CENTER,
             space_before=4, space_after=0)

    # ══════════════════════════════════════════════════════════════════
    # PAGE 27 — Continuation / Additional Notes page
    # ══════════════════════════════════════════════════════════════════
    doc.add_page_break()

    # Footer label at top (matches PDF page 2 layout)
    add_para(doc,
             "Department of Artificial Intelligence & Machine Learning, TCET  |  Major Project I Weekly Logbook",
             bold=False, size=8, color=(80, 80, 80),
             align=WD_ALIGN_PARAGRAPH.CENTER,
             space_before=0, space_after=6)

    # Page 2 has a single 4-column blank table (for additional notes/observations)
    add_centered_para(doc, "Additional Remarks / Observations",
                      bold=True, size=10, space_before=2, space_after=4)

    notes_tbl = doc.add_table(rows=8, cols=1)
    notes_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(notes_tbl, sz="6")
    for row in notes_tbl.rows:
        set_cell_width(row.cells[0], 8000)
        cell_para(row.cells[0], "", size=10, space_before=16, space_after=16)

    # ─── Save ──────────────────────────────────────────────────────────
    doc.save(output)
    import pathlib
    size_kb = pathlib.Path(output).stat().st_size // 1024
    print(f"[OK] Saved -> {output}  ({size_kb} KB)")


if __name__ == "__main__":
    build("LexGuard_Week3_Diary_Pages26_27.docx")
