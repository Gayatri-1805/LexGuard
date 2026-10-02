import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

DEST_DIR = r"c:\Users\PA\OneDrive\Desktop\Niyatii\LexGuard\diagrams"
os.makedirs(DEST_DIR, exist_ok=True)

def generate_module_architecture_fig():
    """Generates Figure 4.2: Overall LexGuard Module Architecture"""
    fig, ax = plt.subplots(figsize=(8, 2.5), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3.2)
    ax.axis('off')

    # Central Top Node: API Gateway / Core Orchestrator
    box_top = patches.FancyBboxPatch((3.2, 2.1), 3.6, 0.9, boxstyle="round,pad=0.1,rounding_size=0.15",
                                     edgecolor="#2563eb", facecolor="#eff6ff", lw=1.5)
    ax.add_patch(box_top)
    ax.text(5.0, 2.65, "FastAPI Service Layer\n(Unified Detection API Gateway)",
            ha='center', va='center', fontsize=9.5, fontweight='bold', color="#1e3a8a")

    # Module 1: Client SDKs
    box_m1 = patches.FancyBboxPatch((0.4, 0.3), 2.7, 1.2, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    edgecolor="#059669", facecolor="#ecfdf5", lw=1.5)
    ax.add_patch(box_m1)
    ax.text(1.75, 1.15, "Module 1: Client SDK Layer", ha='center', va='center', fontsize=9, fontweight='bold', color="#065f46")
    ax.text(1.75, 0.7, "(Python SDK + TypeScript SDK\nAsync Fire-and-Forget Logging)\n[COMPLETED & VERIFIED]",
            ha='center', va='center', fontsize=7.5, color="#047857")

    # Module 2: Detection Engine
    box_m2 = patches.FancyBboxPatch((3.65, 0.3), 2.7, 1.2, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    edgecolor="#7c3aed", facecolor="#f5f3ff", lw=1.5)
    ax.add_patch(box_m2)
    ax.text(5.0, 1.15, "Module 2: Detection Engine", ha='center', va='center', fontsize=9, fontweight='bold', color="#5b21b6")
    ax.text(5.0, 0.7, "(Claim Decomposition + FAISS\nGrounding + LLM-as-a-Judge)\n[COMPLETED & VERIFIED]",
            ha='center', va='center', fontsize=7.5, color="#6d28d9")

    # Module 3: Diagnostic Dashboard
    box_m3 = patches.FancyBboxPatch((6.9, 0.3), 2.7, 1.2, boxstyle="round,pad=0.1,rounding_size=0.15",
                                    edgecolor="#d97706", facecolor="#fffbeb", lw=1.5)
    ax.add_patch(box_m3)
    ax.text(8.25, 1.15, "Module 3: Analytics & Eval", ha='center', va='center', fontsize=9, fontweight='bold', color="#92400e")
    ax.text(8.25, 0.7, "(Neon Postgres + Next.js UI +\nGold Benchmark Harness)\n[COMPLETED & VERIFIED]",
            ha='center', va='center', fontsize=7.5, color="#b45309")

    # Connecting Lines
    ax.annotate('', xy=(1.75, 1.6), xytext=(4.0, 2.1),
                arrowprops=dict(arrowstyle="-|>", color="#4b5563", lw=1.2, shrinkA=2, shrinkB=2))
    ax.annotate('', xy=(5.0, 1.6), xytext=(5.0, 2.1),
                arrowprops=dict(arrowstyle="-|>", color="#4b5563", lw=1.2, shrinkA=2, shrinkB=2))
    ax.annotate('', xy=(8.25, 1.6), xytext=(6.0, 2.1),
                arrowprops=dict(arrowstyle="-|>", color="#4b5563", lw=1.2, shrinkA=2, shrinkB=2))

    out_file = os.path.join(DEST_DIR, "fig4_2_module_architecture.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_file)

def generate_grounding_pipeline_fig():
    """Generates Figure 4.4: Knowledge Base Grounding & Vector Retrieval Pipeline"""
    fig, ax = plt.subplots(figsize=(8.5, 1.6), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.8)
    ax.axis('off')

    steps = [
        ("Candidate\nClaim Input", "#eff6ff", "#2563eb", "#1e3a8a"),
        ("Embeddings\n(all-MiniLM-L6-v2)", "#f5f3ff", "#7c3aed", "#5b21b6"),
        ("384-d FAISS\nVector Index", "#ecfdf5", "#059669", "#065f46"),
        ("Cosine Top-k\nSimilarity Search", "#fffbeb", "#d97706", "#92400e"),
        ("Statutory Context\n& Citation Snippets", "#fef2f2", "#dc2626", "#991b1b")
    ]

    for i, (text, fc, ec, tc) in enumerate(steps):
        x = 0.2 + i * 1.95
        box = patches.FancyBboxPatch((x, 0.2), 1.65, 1.3, boxstyle="round,pad=0.08,rounding_size=0.1",
                                     edgecolor=ec, facecolor=fc, lw=1.2)
        ax.add_patch(box)
        ax.text(x + 0.825, 0.85, text, ha='center', va='center', fontsize=8, fontweight='bold', color=tc)
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(x + 1.9, 0.85), xytext=(x + 1.68, 0.85),
                        arrowprops=dict(arrowstyle="-|>", color="#6b7280", lw=1.3, mutation_scale=10))

    out_file = os.path.join(DEST_DIR, "fig4_4_grounding_pipeline.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_file)

def generate_entailment_pipeline_fig():
    """Generates Figure 4.5: Entailment Verification & Calibrated Trust Scoring Pipeline"""
    fig, ax = plt.subplots(figsize=(8.5, 1.6), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 1.8)
    ax.axis('off')

    steps = [
        ("Claim +\nEvidence Excerpt", "#eff6ff", "#2563eb", "#1e3a8a"),
        ("LLM-as-a-Judge\nPrompting Engine", "#f5f3ff", "#7c3aed", "#5b21b6"),
        ("NLI Verdict Class\n(Support / Contradict)", "#ecfdf5", "#059669", "#065f46"),
        ("Trust Index\nScore Aggregation", "#fffbeb", "#d97706", "#92400e"),
        ("Final Decision\n(SAFE / FLAGGED)", "#fef2f2", "#dc2626", "#991b1b")
    ]

    for i, (text, fc, ec, tc) in enumerate(steps):
        x = 0.2 + i * 1.95
        box = patches.FancyBboxPatch((x, 0.2), 1.65, 1.3, boxstyle="round,pad=0.08,rounding_size=0.1",
                                     edgecolor=ec, facecolor=fc, lw=1.2)
        ax.add_patch(box)
        ax.text(x + 0.825, 0.85, text, ha='center', va='center', fontsize=8, fontweight='bold', color=tc)
        
        if i < len(steps) - 1:
            ax.annotate('', xy=(x + 1.9, 0.85), xytext=(x + 1.68, 0.85),
                        arrowprops=dict(arrowstyle="-|>", color="#6b7280", lw=1.3, mutation_scale=10))

    out_file = os.path.join(DEST_DIR, "fig4_5_verdict_pipeline.png")
    plt.tight_layout()
    plt.savefig(out_file, dpi=300, bbox_inches='tight')
    plt.close()
    print("Generated:", out_file)

if __name__ == "__main__":
    generate_module_architecture_fig()
    generate_grounding_pipeline_fig()
    generate_entailment_pipeline_fig()
