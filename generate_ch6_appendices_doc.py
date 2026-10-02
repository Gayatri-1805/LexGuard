import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def create_chapters_6_to_appendices(filename):
    doc = docx.Document()

    # 1 inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    BODY_COLOR = RGBColor(0x11, 0x18, 0x27)
    
    def add_page_num(paragraph, num_str):
        run = paragraph.add_run(num_str)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def add_chapter_title(ch_num, ch_title, page_no=None):
        if page_no:
            p_top = doc.add_paragraph()
            p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_top.paragraph_format.space_after = Pt(12)
            add_page_num(p_top, str(page_no))

        p_ch = doc.add_paragraph()
        p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ch.paragraph_format.space_before = Pt(0)
        p_ch.paragraph_format.space_after = Pt(4)
        run_ch = p_ch.add_run(f"CHAPTER {ch_num}")
        run_ch.font.name = 'Times New Roman'
        run_ch.font.size = Pt(14)
        run_ch.font.bold = True
        run_ch.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

        p_ti = doc.add_paragraph()
        p_ti.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_ti.paragraph_format.space_before = Pt(0)
        p_ti.paragraph_format.space_after = Pt(20)
        run_ti = p_ti.add_run(ch_title.upper())
        run_ti.font.name = 'Times New Roman'
        run_ti.font.size = Pt(14)
        run_ti.font.bold = True
        run_ti.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

    def add_section_heading(sec_num_title):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        run = p.add_run(sec_num_title)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)
        return p

    def add_body_paragraph(text, space_after=8):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.35
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(space_after)
        run = p.add_run(text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(11.5)
        run.font.color.rgb = BODY_COLOR
        return p

    def add_bullet(bold_prefix, text):
        p = doc.add_paragraph(style='List Bullet')
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(6)
        run_b = p.add_run(bold_prefix)
        run_b.font.name = 'Times New Roman'
        run_b.font.size = Pt(11.5)
        run_b.font.bold = True
        run_b.font.color.rgb = BODY_COLOR
        
        run_t = p.add_run(text)
        run_t.font.name = 'Times New Roman'
        run_t.font.size = Pt(11.5)
        run_t.font.color.rgb = BODY_COLOR
        return p

    def add_numbered_item(num_str, bold_prefix, text):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(6)
        
        run_n = p.add_run(num_str + " ")
        run_n.font.name = 'Times New Roman'
        run_n.font.size = Pt(11.5)
        run_n.font.bold = True
        run_n.font.color.rgb = BODY_COLOR

        if bold_prefix:
            run_b = p.add_run(bold_prefix + ": ")
            run_b.font.name = 'Times New Roman'
            run_b.font.size = Pt(11.5)
            run_b.font.bold = True
            run_b.font.color.rgb = BODY_COLOR

        run_t = p.add_run(text)
        run_t.font.name = 'Times New Roman'
        run_t.font.size = Pt(11.5)
        run_t.font.color.rgb = BODY_COLOR
        return p

    # PAGE 8: CHAPTER 6
    add_chapter_title("6", "Conclusion & Future Scope", page_no=8)
    add_section_heading("6.1 Summary of Work Completed")
    add_body_paragraph(
        "This project set out to design and build LexGuard, an Explainable AI-driven legal hallucination detection platform that bridges the critical gap between generative language model output and authoritative legal ground truth. That goal has been accomplished through the delivery of a production-ready, multi-stage detection ecosystem comprising a high-performance FastAPI detection service, FAISS vector retrieval grounding, an LLM-as-a-judge entailment verification framework, client SDKs (Python and TypeScript), a serverless PostgreSQL analytics store (Neon), and a real-time Next.js diagnostic dashboard."
    )
    add_body_paragraph(
        "Throughout development, the project emphasized deterministic grounding, explainability by default, and honest baseline evaluation over inflated synthetic accuracy claims. The resulting system successfully demonstrates that LLM-generated legal content can be audited, broken down into atomic factual claims, and cross-referenced against statutory ground truth to generate transparent trust scores and actionable routing decisions."
    )

    add_section_heading("6.2 Future Scope")
    add_body_paragraph(
        "Building upon the verified foundation of the current implementation, the following key directions have been identified for future research and engineering:"
    )

    add_bullet("Reintegration of External Fallback Search: ", "Activating and productionizing the multi-source fallback retrieval pipeline (Google Custom Search API and LawCite parser) to dynamically verify unindexed case precedents and recent legal amendments.")
    add_bullet("Implementation of Metamorphic Consistency Testing (Stage 3): ", "Developing metamorphic relation suites (e.g., transitive implication checks, polarity inversion, entity perturbation) to identify subtle logical hallucinations in complex legal reasoning.")
    add_bullet("Semantic Entropy & Pre-Retrieval Risk Triage (Stage 1): ", "Integrating token-level uncertainty estimation and semantic entropy scoring to filter subjective and non-falsifiable text prior to vector lookup, optimizing latency and token expenditure.")

    doc.add_page_break()

    # PAGE 9
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "9")

    add_bullet("Knowledge Base Expansion: ", "Scaling the authoritative legal corpus from 115 IT Act sections to comprehensive national statutory repositories (including Bharatiya Nyaya Sanhita, Commercial Courts Act, and Supreme Court judgments).")
    add_bullet("Domain-Adapted Open NLI Models: ", "Fine-tuning localized open-source Natural Language Inference models (such as Legal-RoBERTa or DeBERTa-v3) to perform entailment checking locally without relying on external commercial LLM APIs.")
    add_bullet("Interactive Human-in-the-Loop Triage: ", "Enhancing the Next.js dashboard with interactive feedback loops, allowing legal practitioners to annotate borderline claims, correct evidence links, and continuously enrich the knowledge repository.")

    add_body_paragraph(
        "Taken together, these directions extend the current, verified foundation of LexGuard toward a robust, multi-jurisdictional AI compliance and verification platform, upholding factual accuracy, transparency, and accountability across legal AI applications."
    )

    doc.add_page_break()

    # PAGE 10: REFERENCES
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "10")

    p_ref_title = doc.add_paragraph()
    p_ref_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ref_title.paragraph_format.space_before = Pt(0)
    p_ref_title.paragraph_format.space_after = Pt(16)
    r_rf = p_ref_title.add_run("REFERENCES")
    r_rf.font.name = 'Times New Roman'
    r_rf.font.size = Pt(14)
    r_rf.font.bold = True
    r_rf.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    references = [
        "[1] L. Huang, W. Yu, W. Ma, W. Zhong, Z. Feng, H. Wang, Q. Chen, W. Peng, X. Feng, B. Qin, and T. Liu, “A Survey on Hallucination in Large Language Models: Principles, Taxonomy, Challenges, and Open Questions,” ACM Transactions on Information Systems, 2024.",
        "[2] M. Dahl, V. Magesh, M. Suzgun, and D. E. Ho, “Large Legal Fictions: Profiling Legal Hallucinations in Large Language Models,” Journal of Legal Analysis, vol. 16, p. 64, 2024.",
        "[3] V. Ovcharov, “Citation Grounding: Detecting and Reducing LLM Citation Hallucinations via Legal Citation Graphs,” arXiv:2606.00898, 2026.",
        "[4] P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks,” Advances in Neural Information Processing Systems, vol. 33, 2020.",
        "[5] L. Zheng, W. Chiang, Y. Sheng, S. Zhuang, Z. Wu, Y. Zhuang, Z. Lin, Z. Li, D. Li, E. P. Xing, H. Zhang, J. E. Gonzalez, and I. Stoica, “Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,” Advances in Neural Information Processing Systems, vol. 36, 2023.",
        "[6] X. Du, C. Xiao, and Y. Li, “HaloScope: Harnessing Unlabeled LLM Generations for Hallucination Detection,” Advances in Neural Information Processing Systems, vol. 37, 2024.",
        "[7] C. Sok, D. Luz, and Y. Haddam, “MetaRAG: Metamorphic Testing for Hallucination Detection in RAG Systems,” arXiv:2509.09360, 2025.",
        "[8] P. Elchafei and M. Abu-Elkheir, “Hallucination Detectives at SemEval-2025 Task 3: Span-Level Hallucination Detection for LLM-Generated Answers,” Proceedings of SemEval-2025, Task 3, 2025.",
        "[9] J. Johnson, M. Douze, and H. Jégou, “Billion-scale similarity search with GPUs,” IEEE Transactions on Big Data, 2019.",
        "[10] N. Reimers and I. Gurevych, “Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks,” Proceedings of EMNLP-IJCNLP, 2019."
    ]

    for ref in references:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(ref)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
        run.font.color.rgb = BODY_COLOR

    doc.add_page_break()

    # PAGE 11: RESEARCH PAPER
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "11")

    p_rp = doc.add_paragraph()
    p_rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_rp.paragraph_format.space_before = Pt(0)
    p_rp.paragraph_format.space_after = Pt(20)
    r_rp = p_rp.add_run("RESEARCH PAPER")
    r_rp.font.name = 'Times New Roman'
    r_rp.font.size = Pt(14)
    r_rp.font.bold = True
    r_rp.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    add_body_paragraph(
        "The work presented in this report was consolidated into a research paper titled “LexGuard: A Multi-Stage Pipeline for Legal LLM Hallucination Detection and Factual Grounding” and submitted for conference review under Multicon 2026."
    )
    add_body_paragraph(
        "Authors: Team HALO (Gayatri Bhosale, Niyati Patel, Paarth Agarwal), under the guidance of Project Supervisor."
    )
    add_body_paragraph(
        "The manuscript (6 pages, 3,840 words) was checked for originality through the department's Turnitin account prior to submission and returned an overall similarity score of 2%, with no unresolved integrity flags. The full similarity report is reproduced in Appendix D, and the corresponding publication entry is listed in Appendix C."
    )

    doc.add_page_break()

    # PAGE 12: APPENDIX A
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "12")

    p_ap_a = doc.add_paragraph()
    p_ap_a.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_a.paragraph_format.space_before = Pt(0)
    p_ap_a.paragraph_format.space_after = Pt(4)
    r_a = p_ap_a.add_run("APPENDIX A")
    r_a.font.name = 'Times New Roman'
    r_a.font.size = Pt(14)
    r_a.font.bold = True
    r_a.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    p_ap_sub = doc.add_paragraph()
    p_ap_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_sub.paragraph_format.space_before = Pt(0)
    p_ap_sub.paragraph_format.space_after = Pt(16)
    r_as = p_ap_sub.add_run("Abbreviations and Symbols")
    r_as.font.name = 'Times New Roman'
    r_as.font.size = Pt(13)
    r_as.font.bold = True
    r_as.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

    abbreviations = [
        ("1.", "AI", "Artificial Intelligence"),
        ("2.", "LLM", "Large Language Model"),
        ("3.", "NLP", "Natural Language Processing"),
        ("4.", "NLI", "Natural Language Inference"),
        ("5.", "KB", "Knowledge Base"),
        ("6.", "FAISS", "Facebook AI Similarity Search"),
        ("7.", "RAG", "Retrieval-Augmented Generation"),
        ("8.", "SDK", "Software Development Kit"),
        ("9.", "API", "Application Programming Interface"),
        ("10.", "REST", "Representational State Transfer"),
        ("11.", "ORM", "Object-Relational Mapping"),
        ("12.", "TI", "Trust Index"),
        ("13.", "JSON", "JavaScript Object Notation"),
        ("14.", "JSONL", "JavaScript Object Notation Lines"),
        ("15.", "IT Act", "Information Technology Act, 2000"),
        ("16.", "PII", "Personally Identifiable Information"),
        ("17.", "UI", "User Interface"),
        ("18.", "UX", "User Experience"),
        ("19.", "AUC", "Area Under the ROC Curve"),
        ("20.", "ROC", "Receiver Operating Characteristic"),
        ("21.", "F1", "Harmonic Mean of Precision and Recall"),
        ("22.", "SQL", "Structured Query Language"),
        ("23.", "TCET", "Thakur College of Engineering & Technology"),
        ("24.", "UoM", "University of Mumbai"),
        ("25.", "AICTE", "All India Council for Technical Education")
    ]

    for num_str, abbr, full in abbreviations:
        add_numbered_item(num_str, abbr, full)

    doc.add_page_break()

    # PAGE 13: APPENDIX B
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "13")

    p_ap_b = doc.add_paragraph()
    p_ap_b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_b.paragraph_format.space_before = Pt(0)
    p_ap_b.paragraph_format.space_after = Pt(4)
    r_b = p_ap_b.add_run("APPENDIX B")
    r_b.font.name = 'Times New Roman'
    r_b.font.size = Pt(14)
    r_b.font.bold = True
    r_b.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    p_ap_sub_b = doc.add_paragraph()
    p_ap_sub_b.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_sub_b.paragraph_format.space_before = Pt(0)
    p_ap_sub_b.paragraph_format.space_after = Pt(16)
    r_bs = p_ap_sub_b.add_run("Definitions")
    r_bs.font.name = 'Times New Roman'
    r_bs.font.size = Pt(13)
    r_bs.font.bold = True
    r_bs.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

    definitions = [
        ("26.", "Legal Hallucination", "The generation of fabricated, inaccurate, or ungrounded assertions by an AI model, including non-existent statutory sections, fictitious case citations, or misrepresented legal holdings."),
        ("27.", "Atomic Claim Decomposition", "The systematic process of deconstructing complex, multi-sentence legal text into standalone, single-fact assertions that can be independently evaluated for factual truth."),
        ("28.", "Knowledge Base Grounding", "The deterministic verification of an extracted claim by comparing its semantic representation against verified statutory and case law text stored in an indexed repository."),
        ("29.", "Natural Language Inference (NLI)", "A computational task that determines whether a given hypothesis (extracted claim) is logically entailed by, contradictory to, or neutral with respect to a provided premise (statutory evidence)."),
        ("30.", "LLM-as-a-Judge", "A paradigm where a zero-shot or few-shot prompted Large Language Model evaluates the factual alignment and entailment between candidate claims and reference evidence."),
        ("31.", "Trust Index (TI)", "A normalized quantitative metric (ranging from 0.0 to 1.0) indicating the overall reliability of an input text, computed from the weighted aggregation of its constituent claim verdicts."),
        ("32.", "Vector Retrieval", "An information retrieval technique using dense vector embeddings (generated by transformer models) to measure cosine similarity between query text and knowledge base documents."),
        ("33.", "Fallback Web Search", "An auxiliary retrieval pipeline that queries external legal databases and search engines when a candidate claim is missing from the local static knowledge base."),
        ("34.", "Metamorphic Consistency", "A software testing and validation methodology that verifies whether an AI model maintains logical and factual consistency under semantic perturbations and transformations.")
    ]

    for num_str, term, defn in definitions:
        add_numbered_item(num_str, term, defn)

    doc.add_page_break()

    # PAGE 14: APPENDIX C
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "14")

    p_ap_c = doc.add_paragraph()
    p_ap_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_c.paragraph_format.space_before = Pt(0)
    p_ap_c.paragraph_format.space_after = Pt(4)
    r_c = p_ap_c.add_run("APPENDIX C")
    r_c.font.name = 'Times New Roman'
    r_c.font.size = Pt(14)
    r_c.font.bold = True
    r_c.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    p_ap_sub_c = doc.add_paragraph()
    p_ap_sub_c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_sub_c.paragraph_format.space_before = Pt(0)
    p_ap_sub_c.paragraph_format.space_after = Pt(16)
    r_cs = p_ap_sub_c.add_run("List of Publications")
    r_cs.font.name = 'Times New Roman'
    r_cs.font.size = Pt(13)
    r_cs.font.bold = True
    r_cs.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

    add_body_paragraph(
        "[1] Gayatri Bhosale, Niyati Patel, Paarth Agarwal, and Project Supervisor, “LexGuard: A Multi-Stage Pipeline for Legal LLM Hallucination Detection and Factual Grounding,” paper submitted to Multicon 2026 [add conference/journal details, volume, page numbers, and DOI upon publication]."
    )
    add_body_paragraph(
        "The originality of the manuscript was verified through the department's Turnitin account prior to submission (Submission ID: trn:oid:::3618:140292811), returning an overall similarity of 2%. The corresponding plagiarism report is attached in Appendix D."
    )

    doc.add_page_break()

    # PAGE 15: APPENDIX D
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "15")

    p_ap_d = doc.add_paragraph()
    p_ap_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_d.paragraph_format.space_before = Pt(0)
    p_ap_d.paragraph_format.space_after = Pt(4)
    r_d = p_ap_d.add_run("APPENDIX D")
    r_d.font.name = 'Times New Roman'
    r_d.font.size = Pt(14)
    r_d.font.bold = True
    r_d.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    p_ap_sub_d = doc.add_paragraph()
    p_ap_sub_d.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ap_sub_d.paragraph_format.space_before = Pt(0)
    p_ap_sub_d.paragraph_format.space_after = Pt(16)
    r_ds = p_ap_sub_d.add_run("Plagiarism Report")
    r_ds.font.name = 'Times New Roman'
    r_ds.font.size = Pt(13)
    r_ds.font.bold = True
    r_ds.font.color.rgb = RGBColor(0x2E, 0x5B, 0x88)

    add_body_paragraph(
        "The following pages reproduce the Turnitin originality report generated from the department's Turnitin account for the paper “LexGuard: A Multi-Stage Pipeline for Legal LLM Hallucination Detection and Factual Grounding,” confirming an overall similarity of 2% with no integrity flags raised for review."
    )

    p_box = doc.add_paragraph()
    p_box.paragraph_format.space_before = Pt(14)
    p_box.paragraph_format.space_after = Pt(6)
    run_bx = p_box.add_run("Turnitin Originality Report Summary:")
    run_bx.font.name = 'Times New Roman'
    run_bx.font.bold = True
    run_bx.font.size = Pt(11.5)

    doc_details = [
        ("Submission ID:", "trn:oid:::3618:140292811"),
        ("Submission Date:", "March 2026"),
        ("Word Count:", "3,840 Words"),
        ("Character Count:", "19,250 Characters"),
        ("File Name:", "LexGuard_Multicon_Paper.pdf")
    ]
    for k, v in doc_details:
        add_bullet(k + " ", v)

    doc.add_page_break()

    # PAGE 16
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_page_num(p_top, "16")

    p_sim = doc.add_paragraph()
    p_sim.paragraph_format.space_before = Pt(10)
    p_sim.paragraph_format.space_after = Pt(8)
    r_sim = p_sim.add_run("2% Overall Similarity")
    r_sim.font.name = 'Times New Roman'
    r_sim.font.size = Pt(13)
    r_sim.font.bold = True
    r_sim.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    add_body_paragraph("The combined total of all matches including overlapping sources, for each database:")

    p_flt = doc.add_paragraph()
    p_flt.paragraph_format.space_before = Pt(6)
    p_flt.paragraph_format.space_after = Pt(4)
    r_flt = p_flt.add_run("Filtered from the Report:")
    r_flt.font.name = 'Times New Roman'
    r_flt.font.bold = True
    r_flt.font.size = Pt(11)

    add_bullet("Bibliography: ", "Excluded from matching")
    add_bullet("Quoted Material: ", "Excluded from matching (< 1% threshold)")

    p_src = doc.add_paragraph()
    p_src.paragraph_format.space_before = Pt(10)
    p_src.paragraph_format.space_after = Pt(4)
    r_src = p_src.add_run("Top Sources Breakdown:")
    r_src.font.name = 'Times New Roman'
    r_src.font.bold = True
    r_src.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)

    add_bullet("Internet Sources: ", "0%")
    add_bullet("Publications: ", "0%")
    add_bullet("Submitted Works (Student Papers): ", "2%")

    p_int = doc.add_paragraph()
    p_int.paragraph_format.space_before = Pt(14)
    p_int.paragraph_format.space_after = Pt(4)
    r_int = p_int.add_run("Integrity Flags:")
    r_int.font.name = 'Times New Roman'
    r_int.font.bold = True
    r_int.font.size = Pt(11)

    add_body_paragraph("0 Integrity Flags for Review. Our system's algorithms look deeply at a document for any inconsistencies that would set it apart from a normal submission. No flags were identified.")

    doc.save(filename)
    print(f"Created {filename}")

if __name__ == "__main__":
    out_path = r"c:\Users\PA\OneDrive\Desktop\Niyatii\LexGuard\LexGuard_BlueBook_Chapters_6_to_Appendices.docx"
    create_chapters_6_to_appendices(out_path)
