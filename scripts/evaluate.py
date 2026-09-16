import os
import sys
import json
import time
import yaml
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import ConversationLoader
from src.evaluation.evaluate_all import FullBenchmarkEvaluator

def run_evaluation():
    start_time = time.time()
    print("=" * 70)
    print("RUNNING RESOLVETRACE BENCHMARK EVALUATION & ABLATION SUITE")
    print("=" * 70)

    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 1. Load training records for baselines and indexing
    turn_csv_path = config['paths']['spotify_turn_csv']
    print(f"Loading training turns from {turn_csv_path}...")
    df_turns = pd.read_csv(turn_csv_path)
    # Filter training sample
    training_records = df_turns.head(15000).to_dict('records')
    print(f"Loaded {len(training_records):,} training turn records.")

    # 2. Load Golden Evaluation Benchmark
    golden_path = config['paths']['golden_set_csv']
    print(f"Loading Golden Evaluation Set from {golden_path}...")
    df_golden = pd.read_csv(golden_path)
    print(f"Loaded {len(df_golden)} golden benchmark test cases.")

    # 3. Instantiate Evaluator
    evaluator = FullBenchmarkEvaluator(
        training_records=training_records,
        playbook_path=config['paths']['playbook_json'],
        thresholds_path="configs/thresholds.yaml"
    )

    # 4. Run Benchmark
    benchmark_output = evaluator.evaluate_benchmark(df_golden)
    ablation_table = benchmark_output['ablation_table']

    # 5. Print Ablation Table
    print("\n" + "=" * 95)
    print("RESOLVETRACE COMPLETE ABLATION BENCHMARK RESULTS")
    print("=" * 95)
    header = f"{'System':<30} | {'Intent F1':<10} | {'Pathway Acc':<12} | {'Unknown F1':<10} | {'Conflict F1':<11} | {'Quality':<8} | {'False Auto':<11} | {'Coverage':<8}"
    print(header)
    print("-" * 95)

    for sys_name, m in ablation_table.items():
        f1_str = f"{m['intent_macro_f1']:.3f}" if m['intent_macro_f1'] is not None else "—"
        p_acc_str = f"{m['pathway_accuracy']:.3f}" if m['pathway_accuracy'] is not None else "—"
        unk_str = f"{m['unknown_f1']:.3f}" if m['unknown_f1'] is not None else "—"
        conf_str = f"{m['conflict_f1']:.3f}" if m['conflict_f1'] is not None else "—"
        qual_str = f"{m['reply_quality']:.2f}" if m['reply_quality'] is not None else "—"
        false_auto_str = f"{m['false_auto_handling']:.1%}" if m['false_auto_handling'] is not None else "—"
        cov_str = f"{m['coverage']:.1%}" if m['coverage'] is not None else "—"

        print(f"{sys_name:<30} | {f1_str:<10} | {p_acc_str:<12} | {unk_str:<10} | {conf_str:<11} | {qual_str:<8} | {false_auto_str:<11} | {cov_str:<8}")

    print("=" * 95)
    print(f"\nHuman vs Judge Agreement (40 cases): Spearman rho = {benchmark_output['human_judge_agreement']['spearman_rho']:.3f}, MAE = {benchmark_output['human_judge_agreement']['mae']:.3f}")
    if 'significance_tests' in benchmark_output:
        sig = benchmark_output['significance_tests']['mcnemar_pathway_accuracy']
        print(f"McNemar Significance (RT vs RAG): {sig['p_value_display']} (exact p = {sig['exact_p_value']:.4f}, chi2 = {sig['chi2_stat']:.3f}, discordant = {sig['discordant_pairs']})")

    # Print Stratified Pathway Accuracy Table
    print("\n" + "=" * 80)
    print("PATHWAY ACCURACY STRATIFIED BY REAL PLAYBOOK STATUS (207 CASES)")
    print("=" * 80)
    print(f"{'Pathway Stratum':<20} | {'Cases (N)':<10} | {'Share (%)':<10} | {'Correct':<8} | {'Accuracy':<10}")
    print("-" * 80)
    for s, d in benchmark_output['stratified_pathway_accuracy'].items():
        print(f"{s:<20} | {d['cases']:<10} | {d['share']*100:<9.1f}% | {d['correct']:<8} | {d['accuracy']*100:<9.1f}%")
    print("-" * 80)
    total_cases = benchmark_output['summary']['total_test_cases']
    total_correct = sum(d['correct'] for d in benchmark_output['stratified_pathway_accuracy'].values())
    print(f"{'Blended Total':<20} | {total_cases:<10} | 100.0%     | {total_correct:<8} | {total_correct/total_cases*100:<9.1f}%")
    print("=" * 80)

    # 6. Save metrics.json
    metrics_path = config['paths']['metrics_json']
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)
    with open(metrics_path, 'w') as f:
        json.dump(benchmark_output, f, indent=2)
    print(f"\nSaved metrics to {metrics_path}")

    # 7. Generate and save Automation Safety Curve plot
    plot_path = config['paths']['safety_curve_plot']
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    
    plt.figure(figsize=(8, 6), dpi=150)
    
    # Systems to plot: Coverage vs False Auto-Handling Rate
    systems_to_plot = [
        ('Semantic RAG', ablation_table['Semantic RAG']['coverage'], ablation_table['Semantic RAG']['false_auto_handling'], 'red', 'o'),
        ('RAG + Intent', ablation_table['RAG + Intent']['coverage'], ablation_table['RAG + Intent']['false_auto_handling'], 'orange', 's'),
        ('Support Playbook', ablation_table['Support Playbook']['coverage'], ablation_table['Support Playbook']['false_auto_handling'], 'blue', '^'),
        ('+ Conflict/Unknown', ablation_table['+ Conflict/Unknown']['coverage'], ablation_table['+ Conflict/Unknown']['false_auto_handling'], 'purple', 'D'),
        ('ResolveTrace (Full)', ablation_table['+ Drift/Risk (ResolveTrace)']['coverage'], ablation_table['+ Drift/Risk (ResolveTrace)']['false_auto_handling'], 'green', '*')
    ]

    for name, cov, false_rate, color, marker in systems_to_plot:
        plt.scatter(cov * 100, false_rate * 100, color=color, s=140, marker=marker, label=name, zorder=5)
        plt.annotate(
            name,
            (cov * 100, false_rate * 100),
            textcoords="offset points",
            xytext=(10, -5),
            ha='left',
            fontsize=9,
            weight='bold'
        )

    plt.title('Automation Safety Curve: Coverage vs. False Auto-Handling Rate', fontsize=12, fontweight='bold')
    plt.xlabel('Automation Coverage (%)', fontsize=11)
    plt.ylabel('False Auto-Handling Rate (%) [Lower is Safer]', fontsize=11)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.xlim(0, 110)
    plt.ylim(-5, 90)
    plt.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    plt.savefig(plot_path)
    plt.close()
    print(f"Saved Automation Safety Curve plot to {plot_path}")

    print(f"\nEvaluation completed in {time.time() - start_time:.2f}s")

if __name__ == '__main__':
    run_evaluation()
