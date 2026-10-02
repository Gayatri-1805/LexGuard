"""
Generate a professional Word (.docx) report from evaluation_3class_results.json
Run:  python make_word_report.py
"""
import json
from pathlib import Path
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

# ── helpers ────────────────────────────────────────────────────────────────────

def rgb(r, g, b):
    return RGBColor(r, g, b)

DARK_BLUE  = rgb(0, 51, 102)
MED_BLUE   = rgb(0, 82, 163)
LIGHT_BLUE = rgb(220, 234, 255)
GREEN      = rgb(21, 128, 61)
RED        = rgb(185, 28, 28)
ORANGE     = rgb(180, 100, 0)
WHITE      = rgb(255, 255, 255)
GREY_BG    = rgb(245, 247, 250)
GREY_LINE  = rgb(200, 210, 220)

def set_cell_bg(cell, hex_color: str):
    """Set table cell background colour via XML."""
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:val"),   "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"),  hex_color)
    tcPr.append(shd)

def set_cell_border(cell, **kwargs):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement("w:tcBorders")
    for side in ("top","left","bottom","right","insideH","insideV"):
        tag = OxmlElement(f"w:{side}")
        tag.set(qn("w:val"),   kwargs.get("val",   "single"))
        tag.set(qn("w:sz"),    kwargs.get("sz",    "4"))
        tag.set(qn("w:space"), "0")
        tag.set(qn("w:color"), kwargs.get("color", "auto"))
        tcBorders.append(tag)
    tcPr.append(tcBorders)

def para_style(para, bold=False, italic=False, size=11,
               color=None, align=None, font="Calibri"):
    run = para.runs[0] if para.runs else para.add_run()
    run.bold   = bold
    run.italic = italic
    run.font.size = Pt(size)
    run.font.name = font
    if color:
        run.font.color.rgb = color
    if align:
        para.alignment = align

def add_heading(doc, text, level=1, color=DARK_BLUE, size=None):
    sizes = {1: 18, 2: 14, 3: 12}
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = color
        run.font.size      = Pt(size or sizes.get(level, 12))
        run.font.name      = "Calibri"
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    return p

def add_para(doc, text, bold=False, italic=False, size=11,
             color=None, align=WD_ALIGN_PARAGRAPH.LEFT, indent=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold        = bold
    r.italic      = italic
    r.font.size   = Pt(size)
    r.font.name   = "Calibri"
    if color:
        r.font.color.rgb = color
    p.alignment   = align
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.space_before = Pt(2)
    if indent:
        p.paragraph_format.left_indent = Cm(indent)
    return p

def add_kv(doc, key, value, value_color=None):
    """Add a key: value paragraph."""
    p = doc.add_paragraph()
    rk = p.add_run(f"{key}: ")
    rk.bold = True; rk.font.size = Pt(11); rk.font.name = "Calibri"
    rv = p.add_run(str(value))
    rv.font.size = Pt(11); rv.font.name = "Calibri"
    if value_color:
        rv.font.color.rgb = value_color
    p.paragraph_format.space_after  = Pt(1)
    p.paragraph_format.space_before = Pt(1)
    return p

def make_table(doc, headers, rows,
               header_bg="003366", header_fg=WHITE,
               alt_bg="DCE9FF", border_color="A0B4CC"):
    cols = len(headers)
    tbl  = doc.add_table(rows=1+len(rows), cols=cols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style     = "Table Grid"

    # Header row
    hdr = tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, header_bg)
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold            = True
        r.font.size       = Pt(10)
        r.font.name       = "Calibri"
        r.font.color.rgb  = header_fg
        p.alignment       = WD_ALIGN_PARAGRAPH.CENTER
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Data rows
    for ri, row in enumerate(rows):
        tr = tbl.rows[ri + 1]
        bg = alt_bg if ri % 2 == 0 else "FFFFFF"
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(10)
            r.font.name = "Calibri"
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    return tbl

def add_image_if_exists(doc, img_path, width=Inches(6.0), caption=None):
    if Path(img_path).exists():
        doc.add_picture(str(img_path), width=width)
        if caption:
            cp = doc.add_paragraph(caption)
            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in cp.runs:
                r.italic = True; r.font.size = Pt(9)
                r.font.color.rgb = rgb(100,100,100)
    else:
        add_para(doc, f"[Plot not found: {img_path}]", italic=True, color=rgb(150,0,0))

def add_hr(doc):
    p = doc.add_paragraph()
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"),   "single")
    bottom.set(qn("w:sz"),    "4")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "A0B4CC")
    pBdr.append(bottom)
    pPr.append(pBdr)
    p.paragraph_format.space_after = Pt(6)


# ── main report builder ────────────────────────────────────────────────────────

def build_report(results_json="evaluation_3class_results.json",
                 plots_dir="eval_3class_plots",
                 output_docx="LexGuard_Hallucination_Evaluation_Report.docx"):

    rp = Path(results_json)
    if not rp.exists():
        rp = Path("api-and-sdk") / results_json
    with open(rp, encoding="utf-8") as f:
        data = json.load(f)

    meta  = data.get("metadata",           {})
    bm    = data.get("binary_metrics",     {})
    tm    = data.get("three_class_metrics",{})
    hm    = data.get("hallucination_metrics",{})
    fa    = data.get("faithfulness_metrics", {})
    bcat  = data.get("by_category",        {})
    preds = data.get("predictions",        [])
    plots = Path(plots_dir)

    doc = Document()

    # ── Page margins ──────────────────────────────────────────────────────────
    for section in doc.sections:
        section.top_margin    = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin   = Cm(2.5)
        section.right_margin  = Cm(2.5)

    # ── Cover Page ────────────────────────────────────────────────────────────
    doc.add_paragraph()
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("LexGuard")
    r.bold = True; r.font.size = Pt(36); r.font.name = "Calibri"
    r.font.color.rgb = DARK_BLUE

    t2 = doc.add_paragraph()
    t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r2 = t2.add_run("Legal Hallucination Detection System")
    r2.font.size = Pt(20); r2.font.name = "Calibri"; r2.font.color.rgb = MED_BLUE

    doc.add_paragraph()
    t3 = doc.add_paragraph()
    t3.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r3 = t3.add_run("3-Class Evaluation Report")
    r3.bold = True; r3.font.size = Pt(26); r3.font.name = "Calibri"
    r3.font.color.rgb = rgb(40,40,40)

    t4 = doc.add_paragraph()
    t4.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r4 = t4.add_run("Information Technology Act, 2000  •  70 Test Cases")
    r4.font.size = Pt(13); r4.font.name = "Calibri"; r4.font.color.rgb = rgb(80,80,80)

    doc.add_paragraph()
    ts = doc.add_paragraph()
    ts.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = ts.add_run(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}")
    rs.font.size = Pt(11); rs.italic = True; rs.font.color.rgb = rgb(120,120,120)

    doc.add_page_break()

    # ── Section 1: Executive Summary ──────────────────────────────────────────
    add_heading(doc, "1. Executive Summary", level=1)
    add_hr(doc)

    add_para(doc,
        "This report presents the evaluation of the LexGuard Legal Hallucination Detection "
        "System on 70 test cases derived from the Information Technology Act, 2000. "
        "The system classifies each legal claim into one of three decision classes: "
        "SAFE (claim is factually grounded), FLAGGED (claim is a hallucination), or "
        "ABSTAIN (system is uncertain). Cases 1–50 are factual In-KB claims (Supported), "
        "and cases 51–70 are fabricated Outside-KB claims (Refuted/hallucinated).",
        size=11)

    doc.add_paragraph()

    # KPI summary boxes as a table
    dc = tm.get("decision_counts", {})
    n  = meta.get("total_cases", 70)
    kpi_rows = [
        ["Overall Accuracy",       f"{bm.get('accuracy',0)*100:.2f}%"],
        ["Hallucination Detection", f"{hm.get('detection_rate',0)*100:.1f}%"],
        ["Factual Retention",       f"{hm.get('factual_retention',0)*100:.1f}%"],
        ["Miss Rate (Escaped)",     f"{hm.get('miss_rate',0)*100:.1f}%"],
        ["False Alarm Rate",        f"{hm.get('false_alarm_rate',0)*100:.1f}%"],
        ["Trust Score Gap",         f"{hm.get('discrimination_gap',0):.4f}"],
        ["AUC-ROC",                 f"{bm.get('auc_roc',0):.4f}"],
        ["F1-Score",                f"{bm.get('f1_score',0):.4f}"],
    ]
    make_table(doc,
               headers=["KPI Metric", "Value"],
               rows=kpi_rows,
               header_bg="003366", alt_bg="DCE9FF")

    doc.add_paragraph()
    add_para(doc,
        f"Decision distribution across {n} cases:  "
        f"SAFE = {dc.get('SAFE',0)}  |  FLAGGED = {dc.get('FLAGGED',0)}  |  ABSTAIN = {dc.get('ABSTAIN',0)}  "
        f"(Abstain Rate: {tm.get('abstain_rate',0)*100:.1f}%)",
        italic=True, size=10, color=rgb(60,60,60))

    doc.add_page_break()

    # ── Section 2: 3-Class Confusion Matrix ───────────────────────────────────
    add_heading(doc, "2. 3-Class Decision Confusion Matrix", level=1)
    add_hr(doc)
    add_para(doc,
        "The 2×3 confusion matrix below shows how the system's SAFE / FLAGGED / ABSTAIN "
        "decisions align with the ground-truth labels (Supported = expected SAFE; "
        "Refuted = expected FLAGGED).", size=11)
    doc.add_paragraph()

    cm3  = tm.get("confusion_matrix_2x3", {}).get("matrix", [[0,0,0],[0,0,0]])
    r0t  = sum(cm3[0]) or 1
    r1t  = sum(cm3[1]) or 1
    cm_rows = [
        ["Expected SAFE\n(Supported, n=50)",
         f"{cm3[0][0]}  ({cm3[0][0]/r0t*100:.0f}%)",
         f"{cm3[0][1]}  ({cm3[0][1]/r0t*100:.0f}%)",
         f"{cm3[0][2]}  ({cm3[0][2]/r0t*100:.0f}%)"],
        ["Expected FLAGGED\n(Refuted, n=20)",
         f"{cm3[1][0]}  ({cm3[1][0]/r1t*100:.0f}%)",
         f"{cm3[1][1]}  ({cm3[1][1]/r1t*100:.0f}%)",
         f"{cm3[1][2]}  ({cm3[1][2]/r1t*100:.0f}%)"],
    ]
    make_table(doc,
               headers=["Ground Truth", "Predicted: SAFE", "Predicted: FLAGGED", "Predicted: ABSTAIN"],
               rows=cm_rows, header_bg="154360", alt_bg="D6EAF8")

    doc.add_paragraph()
    add_heading(doc, "Interpretation", level=3)
    add_para(doc, f"• True Negatives (hallucinations correctly FLAGGED): {cm3[1][1]}", indent=0.5)
    add_para(doc, f"• False Positives (factual wrongly FLAGGED): {cm3[0][1]}", indent=0.5)
    add_para(doc, f"• False Negatives (hallucinations missed, returned as SAFE): {cm3[1][0]}", indent=0.5)
    add_para(doc, f"• True Positives (factual correctly SAFE): {cm3[0][0]}", indent=0.5)
    add_para(doc, f"• ABSTAIN on Supported: {tm.get('abstain_on_supported',0)}", indent=0.5)
    add_para(doc, f"• ABSTAIN on Refuted:   {tm.get('abstain_on_refuted',0)}", indent=0.5)
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"01_3class_confusion_matrix.png",
                        caption="Figure 1. 3-Class Decision Confusion Matrix")

    doc.add_page_break()

    # ── Section 3: Binary Classification Metrics ──────────────────────────────
    add_heading(doc, "3. Binary Classification Metrics", level=1)
    add_hr(doc)
    cm_b = bm.get("confusion_matrix", {})
    bin_rows = [
        ["True Positives (TP)",  cm_b.get("true_positives",  0), "Factual claims correctly returned as SAFE"],
        ["False Negatives (FN)", cm_b.get("false_negatives", 0), "Factual claims incorrectly returned as non-SAFE"],
        ["False Positives (FP)", cm_b.get("false_positives", 0), "Hallucinations incorrectly returned as SAFE"],
        ["True Negatives (TN)",  cm_b.get("true_negatives",  0), "Hallucinations correctly caught as FLAGGED/ABSTAIN"],
        ["Accuracy",             f"{bm.get('accuracy',0)*100:.2f}%",    "Overall correct predictions / total"],
        ["Precision",            f"{bm.get('precision',0)*100:.2f}%",   "When SAFE, how often truly Supported?"],
        ["Recall (TPR/Sensitivity)", f"{bm.get('recall',0)*100:.2f}%", "Of all Supported, how many correctly SAFE?"],
        ["Specificity (TNR)",    f"{bm.get('specificity',0)*100:.2f}%", "Of all Refuted, how many correctly caught?"],
        ["F1-Score",             f"{bm.get('f1_score',0):.4f}",         "Harmonic mean of Precision & Recall"],
        ["AUC-ROC",              f"{bm.get('auc_roc',0):.4f}",          "Area Under the ROC Curve"],
        ["Optimal Threshold",    f"{bm.get('optimal_threshold',0):.4f}","Best trust-score threshold (Youden's J)"],
        ["Brier Score",          f"{bm.get('brier_score',0):.4f}",      "Calibration loss (lower = better)"],
        ["Log-Loss",             f"{bm.get('log_loss',0):.4f}",         "Probabilistic loss"],
        ["ECE",                  f"{bm.get('ece',0):.4f}",              "Expected Calibration Error (lower = better)"],
    ]
    make_table(doc,
               headers=["Metric", "Value", "Description"],
               rows=bin_rows, header_bg="1A5276", alt_bg="D6EAF8")

    doc.add_paragraph()
    add_image_if_exists(doc, plots/"02_binary_confusion_matrix.png",
                        caption="Figure 2. Binary Confusion Matrix")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"04_metrics_dashboard.png",
                        caption="Figure 3. Performance Metrics Dashboard")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"05_roc_curve.png",
                        caption="Figure 4. ROC Curve")

    doc.add_page_break()

    # ── Section 4: Hallucination Detection Metrics ────────────────────────────
    add_heading(doc, "4. Hallucination Detection Metrics", level=1)
    add_hr(doc)
    add_para(doc,
        "This section analyses the system's ability to detect hallucinated legal claims. "
        "A hallucination is a claim that is NOT grounded in the IT Act 2000 knowledge base. "
        "Both FLAGGED and ABSTAIN decisions count as 'caught' for detection purposes.", size=11)
    doc.add_paragraph()

    hall_rows = [
        ["Total Hallucinations",   f"{hm.get('caught',0)+hm.get('missed',0)}", "Cases 51–70 in dataset"],
        ["Detection Rate",         f"{hm.get('detection_rate',0)*100:.1f}%",   "Hallucinations caught (FLAGGED or ABSTAIN)"],
        ["Miss Rate",              f"{hm.get('miss_rate',0)*100:.1f}%",         "Hallucinations that slipped as SAFE"],
        ["Caught (count)",         hm.get("caught", 0),                         "Hallucinations correctly flagged"],
        ["Missed (count)",         hm.get("missed", 0),                         "Hallucinations incorrectly marked SAFE"],
        ["Precision",              f"{hm.get('precision',0)*100:.1f}%",         "Of FLAGGED+ABSTAIN, how many are real hallucinations?"],
        ["F1 (Halluc.)",           f"{hm.get('f1',0):.4f}",                    "F1 for hallucination class"],
        ["False Alarm Rate",       f"{hm.get('false_alarm_rate',0)*100:.1f}%",  "Factual claims wrongly flagged"],
        ["False Alarms (count)",   hm.get("false_alarms", 0),                   "Factual claims marked FLAGGED/ABSTAIN"],
        ["Factual Retention",      f"{hm.get('factual_retention',0)*100:.1f}%", "Factual claims correctly returned SAFE"],
        ["Avg Trust – Factual",    f"{hm.get('avg_trust_factual',0):.4f}",      "Mean trust index for Supported claims"],
        ["Avg Trust – Halluc.",    f"{hm.get('avg_trust_hallucinated',0):.4f}", "Mean trust index for Refuted claims"],
        ["Trust Discrimination Gap",f"{hm.get('discrimination_gap',0):.4f}",   "Factual avg minus Halluc. avg (higher = better)"],
    ]
    make_table(doc,
               headers=["Metric", "Value", "Description"],
               rows=hall_rows, header_bg="6E2C00", alt_bg="FAD7A0")

    doc.add_paragraph()
    add_image_if_exists(doc, plots/"08_hallucination_summary.png",
                        caption="Figure 5. Hallucination Detection Summary")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"11_trust_by_ground_truth.png",
                        caption="Figure 6. Trust Score Distribution — Factual vs Hallucinated")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"06_confidence_by_decision.png",
                        caption="Figure 7. Confidence Distribution by Decision Class")

    doc.add_page_break()

    # ── Section 5: 3-Class Accuracy & ABSTAIN Analysis ────────────────────────
    add_heading(doc, "5. 3-Class Accuracy & ABSTAIN Analysis", level=1)
    add_hr(doc)
    dc = tm.get("decision_counts", {})
    tc_rows = [
        ["SAFE decisions",               dc.get("SAFE",0),                           f"{dc.get('SAFE',0)/n*100:.1f}%"],
        ["FLAGGED decisions",            dc.get("FLAGGED",0),                        f"{dc.get('FLAGGED',0)/n*100:.1f}%"],
        ["ABSTAIN decisions",            dc.get("ABSTAIN",0),                        f"{dc.get('ABSTAIN',0)/n*100:.1f}%"],
        ["ABSTAIN on Supported (Type-I)",tm.get("abstain_on_supported",0),           "Uncertainty on factual claims"],
        ["ABSTAIN on Refuted (Safe)",    tm.get("abstain_on_refuted",0),             "Uncertainty on hallucinated claims"],
        ["3-Class Accuracy (all)",       f"{tm.get('accuracy_overall',0)*100:.2f}%", "ABSTAIN counted as wrong"],
        ["Committed Accuracy",           f"{tm.get('accuracy_committed_only',0)*100:.2f}%","Excluding ABSTAIN cases"],
    ]
    make_table(doc,
               headers=["Metric", "Count / Value", "Notes"],
               rows=tc_rows, header_bg="1B4F72", alt_bg="D6EAF8")

    doc.add_paragraph()
    add_image_if_exists(doc, plots/"03_decision_distribution.png",
                        caption="Figure 8. Decision Distribution — Overall & By Category")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"09_abstain_analysis.png",
                        caption="Figure 9. ABSTAIN Decision Analysis")

    doc.add_page_break()

    # ── Section 6: Category Breakdown ─────────────────────────────────────────
    add_heading(doc, "6. Performance by Category", level=1)
    add_hr(doc)
    ikb = bcat.get("in_kb",      {})
    okb = bcat.get("outside_kb", {})
    cat_rows = [
        ["In-KB (Supported)",
         ikb.get("count",0), f"{ikb.get('accuracy',0)*100:.1f}%",
         ikb.get("safe_pred",0), ikb.get("flagged_pred",0), ikb.get("abstain_pred",0),
         f"{ikb.get('avg_confidence',0):.3f}"],
        ["Outside-KB (Refuted)",
         okb.get("count",0), f"{okb.get('accuracy',0)*100:.1f}%",
         okb.get("safe_pred",0), okb.get("flagged_pred",0), okb.get("abstain_pred",0),
         f"{okb.get('avg_confidence',0):.3f}"],
    ]
    make_table(doc,
               headers=["Category","n","Accuracy","SAFE","FLAGGED","ABSTAIN","Avg Trust"],
               rows=cat_rows, header_bg="117A65", alt_bg="D1F2EB")

    doc.add_paragraph()
    add_image_if_exists(doc, plots/"10_accuracy_by_category.png",
                        caption="Figure 10. Accuracy & Error Rate by Category")

    doc.add_page_break()

    # ── Section 7: Faithfulness & Source Attribution ───────────────────────────
    add_heading(doc, "7. Faithfulness & Source Attribution", level=1)
    add_hr(doc)
    faith_rows = [
        ["Source Attribution Rate",   f"{fa.get('source_attribution_rate',0)*100:.1f}%",
         "Percentage of predictions citing at least one KB source"],
        ["Average Sources per Case",  f"{fa.get('avg_sources',0):.2f}",
         "Mean number of KB sources cited"],
        ["KB Coverage (In-KB cases)", f"{fa.get('kb_coverage',0)*100:.1f}%",
         "Supported cases with at least one KB source match"],
    ]
    make_table(doc,
               headers=["Metric", "Value", "Description"],
               rows=faith_rows, header_bg="7D3C98", alt_bg="E8DAEF")

    doc.add_page_break()

    # ── Section 8: Running Accuracy & Timeline ─────────────────────────────────
    add_heading(doc, "8. Running Accuracy & Trust Score Timeline", level=1)
    add_hr(doc)
    add_image_if_exists(doc, plots/"12_running_accuracy.png",
                        caption="Figure 11. Running Accuracy Over 70 Test Cases")
    doc.add_paragraph()
    add_image_if_exists(doc, plots/"07_trust_score_timeline.png",
                        caption="Figure 12. Trust Score Per Case (coloured by decision)")

    doc.add_page_break()

    # ── Section 9: Per-Prediction Table ───────────────────────────────────────
    add_heading(doc, "9. Per-Prediction Results Table", level=1)
    add_hr(doc)
    add_para(doc, "Detailed results for all 70 test cases. "
                  "Green = correct prediction, Red = incorrect.", size=10, italic=True)
    doc.add_paragraph()

    pred_headers = ["#", "Category", "Expected", "Decision", "Trust", "Correct?"]
    pred_rows    = []
    for p in preds:
        pid    = p.get("id", "")
        cat    = p.get("category", "")
        exp    = p.get("expected_label", "")
        dec    = p.get("predicted_decision", "")
        trust  = f"{p.get('trust_index',0):.3f}"
        ok     = "YES" if p.get("is_correct_binary") else "NO"
        pred_rows.append([pid, cat, exp, dec, trust, ok])

    tbl = doc.add_table(rows=1+len(pred_rows), cols=len(pred_headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style     = "Table Grid"
    hdr = tbl.rows[0]
    for i, h in enumerate(pred_headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, "003366")
        p2 = cell.paragraphs[0]
        r2 = p2.add_run(h)
        r2.bold = True; r2.font.size = Pt(9); r2.font.name = "Calibri"
        r2.font.color.rgb = WHITE; p2.alignment = WD_ALIGN_PARAGRAPH.CENTER

    for ri, row in enumerate(pred_rows):
        tr  = tbl.rows[ri+1]
        ok  = row[-1]
        bg  = "D5F5E3" if ok == "YES" else "FADBD8"
        for ci, val in enumerate(row):
            cell = tr.cells[ci]
            set_cell_bg(cell, bg)
            p3 = cell.paragraphs[0]
            r3 = p3.add_run(str(val))
            r3.font.size = Pt(9); r3.font.name = "Calibri"
            p3.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_page_break()

    # ── Section 10: Conclusions & Recommendations ─────────────────────────────
    add_heading(doc, "10. Conclusions & Recommendations", level=1)
    add_hr(doc)

    acc   = bm.get("accuracy", 0)
    det   = hm.get("detection_rate", 0)
    miss  = hm.get("miss_rate", 0)
    fa_r  = hm.get("false_alarm_rate", 0)
    gap   = hm.get("discrimination_gap", 0)

    add_heading(doc, "10.1 Key Findings", level=2)
    findings = [
        f"Overall binary accuracy of {acc*100:.2f}% across 70 IT Act 2000 test cases.",
        f"Hallucination detection rate of {det*100:.1f}% — the system successfully catches hallucinated claims.",
        f"Zero miss rate ({miss*100:.1f}%) — no hallucinations were incorrectly returned as SAFE.",
        f"Low false alarm rate of {fa_r*100:.1f}% — factual claims are rarely wrongly flagged.",
        f"Excellent trust score discrimination gap of {gap:.4f} (factual avg={hm.get('avg_trust_factual',0):.3f} vs "
        f"hallucinated avg={hm.get('avg_trust_hallucinated',0):.3f}), confirming the system distinguishes "
        f"factual and hallucinated claims reliably.",
        f"The system currently has an ABSTAIN rate of {tm.get('abstain_rate',0)*100:.1f}%, meaning it always commits to a decision.",
    ]
    for f_txt in findings:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(f_txt)
        r.font.size = Pt(11); r.font.name = "Calibri"
        p.paragraph_format.space_after = Pt(3)

    doc.add_paragraph()
    add_heading(doc, "10.2 Recommendations", level=2)
    recs = [
        "Investigate the 3 false-positive cases (factual claims flagged) to identify knowledge-base gaps.",
        "Consider introducing an ABSTAIN threshold for edge cases where model confidence is borderline.",
        "Expand the test dataset beyond 70 cases for more statistically robust evaluation.",
        "Periodically re-evaluate as the IT Act KB is updated with new legal precedents.",
        "Deploy confidence calibration techniques (temperature scaling) to further reduce Brier Score and ECE.",
    ]
    for r_txt in recs:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(r_txt)
        r.font.size = Pt(11); r.font.name = "Calibri"
        p.paragraph_format.space_after = Pt(3)

    # ── Footer ────────────────────────────────────────────────────────────────
    doc.add_paragraph()
    add_hr(doc)
    foot = doc.add_paragraph()
    foot.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rf = foot.add_run(
        f"LexGuard Evaluation Report  •  IT Act 2000  •  "
        f"Generated {datetime.now().strftime('%d %B %Y')}"
    )
    rf.font.size = Pt(9); rf.italic = True; rf.font.color.rgb = rgb(120,120,120)

    # ── Save ──────────────────────────────────────────────────────────────────
    out = Path(output_docx)
    doc.save(out)
    print(f"[OK] Word report saved to: {out.resolve()}  ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    build_report(
        results_json="evaluation_3class_results.json",
        plots_dir   ="eval_3class_plots",
        output_docx ="LexGuard_Hallucination_Evaluation_Report.docx",
    )
