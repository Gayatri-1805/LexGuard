"""
Results Visualization Tool
==========================

Generates visual diagrams and graphs from test results:
- Accuracy bar charts (overall, by category, by difficulty)
- Confusion matrix heatmap
- Performance metrics (latency, KB hits)
- Trust score distribution
- Error analysis

Requires: matplotlib, seaborn, pandas
Install: pip install matplotlib seaborn pandas
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    import numpy as np
except ImportError:
    print("❌ Required packages not installed.")
    print("   Install with: pip install matplotlib seaborn pandas")
    sys.exit(1)

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_results(json_file: str) -> Dict:
    """Load test results from JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_overall_accuracy(data: Dict, output_dir: str = "."):
    """Plot overall accuracy metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('📊 Overall Performance Metrics', fontsize=16, fontweight='bold')
    
    metrics = data['metrics']
    
    # 1. Overall Accuracy Gauge
    ax = axes[0, 0]
    accuracy = metrics['accuracy']
    categories = ['Correct', 'Incorrect']
    values = [metrics['correct'], metrics['total_cases'] - metrics['correct']]
    colors = ['#2ecc71', '#e74c3c']
    
    wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%',
                                        colors=colors, startangle=90)
    ax.set_title(f"Overall Accuracy: {accuracy:.1%}", fontweight='bold')
    
    # 2. Accuracy by Category
    ax = axes[0, 1]
    by_cat = metrics['by_category']
    categories = list(by_cat.keys())
    accuracies = [by_cat[cat]['accuracy'] for cat in categories]
    colors_bar = ['#2ecc71' if acc >= 0.8 else '#f39c12' if acc >= 0.6 else '#e74c3c' for acc in accuracies]
    
    bars = ax.barh(categories, accuracies, color=colors_bar)
    ax.set_xlim(0, 1.0)
    ax.set_xlabel('Accuracy')
    ax.set_title('Accuracy by Category', fontweight='bold')
    ax.axvline(x=0.8, color='green', linestyle='--', alpha=0.5, label='Target: 80%')
    
    # Add value labels
    for i, (bar, acc) in enumerate(zip(bars, accuracies)):
        ax.text(acc + 0.02, bar.get_y() + bar.get_height()/2, 
                f'{acc:.1%}', va='center', fontweight='bold')
    
    # 3. Accuracy by Difficulty
    ax = axes[1, 0]
    by_diff = metrics['by_difficulty']
    difficulties = list(by_diff.keys())
    accuracies_diff = [by_diff[diff]['accuracy'] for diff in difficulties]
    colors_diff = ['#3498db', '#9b59b6', '#e67e22'][:len(difficulties)]
    
    bars = ax.bar(difficulties, accuracies_diff, color=colors_diff, alpha=0.7)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel('Accuracy')
    ax.set_title('Accuracy by Difficulty', fontweight='bold')
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5, label='Target: 80%')
    ax.legend()
    
    # Add value labels
    for bar, acc in zip(bars, accuracies_diff):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.02,
                f'{acc:.1%}', ha='center', va='bottom', fontweight='bold')
    
    # 4. Key Metrics Summary
    ax = axes[1, 1]
    ax.axis('off')
    
    summary_text = f"""
    📈 KEY METRICS
    
    Total Test Cases: {metrics['total_cases']}
    Correct Predictions: {metrics['correct']}
    Overall Accuracy: {metrics['accuracy']:.1%}
    
    Performance:
    • Avg Processing Time: {metrics['avg_processing_time']:.2f}s
    • KB Hit Rate: {metrics['avg_kb_hit_rate']:.1%}
    • Total KB Hits: {metrics['total_kb_hits']}
    • Total Claims: {metrics['total_claims']}
    
    Errors: {metrics['errors']}
    """
    
    ax.text(0.1, 0.5, summary_text, fontsize=11, family='monospace',
            verticalalignment='center')
    
    plt.tight_layout()
    output_file = f"{output_dir}/overall_accuracy.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()

def plot_confusion_matrix(data: Dict, output_dir: str = "."):
    """Plot confusion matrix as heatmap."""
    metrics = data['metrics']
    confusion = metrics['confusion_matrix']
    
    # Parse confusion matrix into 2D array
    decisions = ['SAFE', 'ABSTAIN', 'FLAGGED', 'ERROR']
    matrix = np.zeros((len(decisions), len(decisions)))
    
    for transition, count in confusion.items():
        if ' → ' in transition:
            expected, actual = transition.split(' → ')
            if expected in decisions and actual in decisions:
                i = decisions.index(expected)
                j = decisions.index(actual)
                matrix[i, j] = count
    
    # Create heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(matrix, annot=True, fmt='.0f', cmap='YlOrRd', 
                xticklabels=decisions, yticklabels=decisions,
                cbar_kws={'label': 'Count'}, ax=ax)
    
    ax.set_xlabel('Actual Decision', fontweight='bold')
    ax.set_ylabel('Expected Decision', fontweight='bold')
    ax.set_title('🔀 Confusion Matrix', fontsize=14, fontweight='bold', pad=20)
    
    # Highlight diagonal (correct predictions)
    for i in range(len(decisions)):
        ax.add_patch(plt.Rectangle((i, i), 1, 1, fill=False, 
                                   edgecolor='green', lw=3))
    
    plt.tight_layout()
    output_file = f"{output_dir}/confusion_matrix.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()

def plot_performance_metrics(data: Dict, output_dir: str = "."):
    """Plot performance metrics (latency, KB hits)."""
    results = data['results']
    df = pd.DataFrame(results)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('⚡ Performance Metrics', fontsize=16, fontweight='bold')
    
    # 1. Processing Time Distribution
    ax = axes[0, 0]
    df['processing_time'].hist(bins=20, color='#3498db', alpha=0.7, ax=ax)
    ax.axvline(df['processing_time'].mean(), color='red', linestyle='--', 
               label=f'Mean: {df["processing_time"].mean():.2f}s')
    ax.set_xlabel('Processing Time (seconds)')
    ax.set_ylabel('Frequency')
    ax.set_title('Processing Time Distribution', fontweight='bold')
    ax.legend()
    
    # 2. KB Hit Rate by Category
    ax = axes[0, 1]
    category_kb = df.groupby('category').apply(
        lambda x: x['kb_hits'].sum() / x['claims_count'].sum() if x['claims_count'].sum() > 0 else 0
    )
    category_kb.plot(kind='bar', color='#2ecc71', alpha=0.7, ax=ax)
    ax.set_ylabel('KB Hit Rate')
    ax.set_title('KB Hit Rate by Category', fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
    ax.axhline(y=0.5, color='orange', linestyle='--', alpha=0.5, label='Target: 50%')
    ax.legend()
    
    # 3. Trust Score Distribution
    ax = axes[1, 0]
    correct = df[df['correct'] == True]['trust_index']
    incorrect = df[df['correct'] == False]['trust_index']
    
    ax.hist([correct, incorrect], bins=20, label=['Correct', 'Incorrect'],
            color=['#2ecc71', '#e74c3c'], alpha=0.6)
    ax.set_xlabel('Trust Index')
    ax.set_ylabel('Frequency')
    ax.set_title('Trust Score Distribution', fontweight='bold')
    ax.legend()
    
    # 4. Claims vs KB Hits Scatter
    ax = axes[1, 1]
    colors_scatter = df['correct'].map({True: '#2ecc71', False: '#e74c3c'})
    ax.scatter(df['claims_count'], df['kb_hits'], c=colors_scatter, alpha=0.6, s=100)
    ax.set_xlabel('Claims Count')
    ax.set_ylabel('KB Hits')
    ax.set_title('Claims vs KB Hits', fontweight='bold')
    ax.plot([0, df['claims_count'].max()], [0, df['claims_count'].max()], 
            'k--', alpha=0.3, label='Perfect KB Hit')
    ax.legend(['Perfect KB Hit', 'Correct', 'Incorrect'])
    
    plt.tight_layout()
    output_file = f"{output_dir}/performance_metrics.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()

def plot_detailed_analysis(data: Dict, output_dir: str = "."):
    """Plot detailed analysis charts."""
    results = data['results']
    df = pd.DataFrame(results)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('🔬 Detailed Analysis', fontsize=16, fontweight='bold')
    
    # 1. Accuracy vs Difficulty
    ax = axes[0, 0]
    diff_acc = df.groupby('difficulty')['correct'].mean()
    diff_acc.plot(kind='bar', color='#9b59b6', alpha=0.7, ax=ax)
    ax.set_ylabel('Accuracy')
    ax.set_title('Accuracy by Difficulty Level', fontweight='bold')
    ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
    ax.axhline(y=0.8, color='green', linestyle='--', alpha=0.5)
    
    for i, v in enumerate(diff_acc):
        ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontweight='bold')
    
    # 2. Error Analysis
    ax = axes[0, 1]
    error_counts = df['error'].notna().sum()
    success_counts = df['error'].isna().sum()
    
    ax.bar(['Success', 'Errors'], [success_counts, error_counts],
           color=['#2ecc71', '#e74c3c'], alpha=0.7)
    ax.set_ylabel('Count')
    ax.set_title('Success vs Errors', fontweight='bold')
    
    for i, v in enumerate([success_counts, error_counts]):
        ax.text(i, v + 0.5, str(v), ha='center', fontweight='bold')
    
    # 3. Average Processing Time by Category
    ax = axes[1, 0]
    cat_time = df.groupby('category')['processing_time'].mean()
    cat_time.plot(kind='barh', color='#e67e22', alpha=0.7, ax=ax)
    ax.set_xlabel('Avg Processing Time (seconds)')
    ax.set_title('Processing Time by Category', fontweight='bold')
    
    for i, v in enumerate(cat_time):
        ax.text(v + 0.5, i, f'{v:.1f}s', va='center', fontweight='bold')
    
    # 4. Decision Distribution
    ax = axes[1, 1]
    decision_counts = df['actual'].value_counts()
    colors_decision = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6'][:len(decision_counts)]
    
    decision_counts.plot(kind='pie', autopct='%1.1f%%', colors=colors_decision,
                         ax=ax, startangle=90)
    ax.set_ylabel('')
    ax.set_title('Decision Distribution', fontweight='bold')
    
    plt.tight_layout()
    output_file = f"{output_dir}/detailed_analysis.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_file}")
    plt.close()

def generate_summary_report(data: Dict, output_dir: str = "."):
    """Generate text summary report."""
    metrics = data['metrics']
    
    report = f"""
{'='*80}
COMPREHENSIVE TEST RESULTS SUMMARY
{'='*80}

Test Run: {data['timestamp']}

OVERALL PERFORMANCE
-------------------
Total Test Cases:        {metrics['total_cases']}
Correct Predictions:     {metrics['correct']}
Overall Accuracy:        {metrics['accuracy']:.1%}
Errors:                  {metrics['errors']}

PERFORMANCE METRICS
-------------------
Avg Processing Time:     {metrics['avg_processing_time']:.2f} seconds
KB Hit Rate:             {metrics['avg_kb_hit_rate']:.1%}
Total KB Hits:           {metrics['total_kb_hits']}
Total Claims Extracted:  {metrics['total_claims']}

ACCURACY BY CATEGORY
--------------------
"""
    
    for category, data_cat in sorted(metrics['by_category'].items()):
        accuracy = data_cat['accuracy']
        grade = "✅" if accuracy >= 0.8 else "⚠️" if accuracy >= 0.6 else "❌"
        report += f"{grade} {category:25s}: {data_cat['correct']:2d}/{data_cat['total']:2d} ({accuracy:.1%})\n"
    
    report += f"\nACCURACY BY DIFFICULTY\n----------------------\n"
    
    for difficulty, data_diff in sorted(metrics['by_difficulty'].items()):
        accuracy = data_diff['accuracy']
        grade = "✅" if accuracy >= 0.8 else "⚠️" if accuracy >= 0.6 else "❌"
        report += f"{grade} {difficulty:25s}: {data_diff['correct']:2d}/{data_diff['total']:2d} ({accuracy:.1%})\n"
    
    report += f"\nCONFUSION MATRIX\n----------------\n"
    
    for transition, count in sorted(metrics['confusion_matrix'].items(), key=lambda x: -x[1]):
        report += f"{transition:30s}: {count:2d}\n"
    
    # Final grade
    accuracy = metrics['accuracy']
    if accuracy >= 0.9:
        grade = "A+ (Excellent)"
    elif accuracy >= 0.8:
        grade = "A (Very Good)"
    elif accuracy >= 0.7:
        grade = "B (Good)"
    elif accuracy >= 0.6:
        grade = "C (Fair)"
    else:
        grade = "D (Needs Improvement)"
    
    report += f"\n{'='*80}\n"
    report += f"FINAL GRADE: {grade}\n"
    report += f"{'='*80}\n"
    
    output_file = f"{output_dir}/summary_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Saved: {output_file}")
    return report

def main():
    """Main visualization function."""
    
    if len(sys.argv) < 2:
        print("Usage: python visualize_results.py <results_json_file>")
        print("\nOr use the latest results file automatically:")
        
        # Find latest JSON file
        json_files = list(Path('.').glob('comprehensive_test_*.json'))
        if not json_files:
            print("❌ No test result files found.")
            print("   Run tests first: python run_comprehensive_tests.py")
            return
        
        latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
        print(f"   Using: {latest_file}")
        json_file = str(latest_file)
    else:
        json_file = sys.argv[1]
    
    print(f"\n📊 Loading results from: {json_file}")
    data = load_results(json_file)
    
    # Create output directory
    output_dir = "visualizations"
    Path(output_dir).mkdir(exist_ok=True)
    
    print(f"\n🎨 Generating visualizations...")
    
    # Generate all plots
    plot_overall_accuracy(data, output_dir)
    plot_confusion_matrix(data, output_dir)
    plot_performance_metrics(data, output_dir)
    plot_detailed_analysis(data, output_dir)
    
    # Generate summary report
    print(f"\n📝 Generating summary report...")
    report = generate_summary_report(data, output_dir)
    
    print(f"\n✅ All visualizations saved to: {output_dir}/")
    print(f"\nGenerated files:")
    print(f"   • overall_accuracy.png")
    print(f"   • confusion_matrix.png")
    print(f"   • performance_metrics.png")
    print(f"   • detailed_analysis.png")
    print(f"   • summary_report.txt")
    
    print(f"\n{report}")

if __name__ == "__main__":
    main()
