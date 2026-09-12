import os
import sys
import pandas as pd
import numpy as np
import yaml
import matplotlib.pyplot as plt

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.playbook.store import PlaybookStore
from src.playbook.matcher import PathwayMatcher
from src.decision.engine import DecisionEngine
from src.state.extractor import StateExtractor
from src.classification.tfidf_classifier import TfidfIntentClassifier
from src.drift.monitor import DriftMonitor
from src.evaluation.metrics import EvaluationMetrics

def run_sweep():
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    df_turns = pd.read_csv(config['paths']['spotify_turn_csv'])
    train_recs = df_turns.head(15000).to_dict('records')
    tfidf_clf = TfidfIntentClassifier().fit([r['customer_text'] for r in train_recs], [r['intent'] for r in train_recs])

    store = PlaybookStore(config['paths']['playbook_json'])
    matcher = PathwayMatcher(store.pathways, training_records=train_recs)
    drift_monitor = DriftMonitor().fit_from_records(train_recs)
    df_golden = pd.read_csv(config['paths']['golden_set_csv'])

    gold_messages = df_golden['customer_message'].tolist()
    gold_decisions = df_golden['expected_decision'].tolist()
    gold_should_escalate = df_golden['should_escalate'].tolist()

    threshold_sweep = [0.20, 0.35, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80]
    sweep_results = []

    for thresh in threshold_sweep:
        engine = DecisionEngine(matcher, thresholds_path='configs/thresholds.yaml')
        engine.threshold_auto = thresh
        
        decisions = []
        for msg in gold_messages:
            intent, conf = tfidf_clf.predict_with_confidence(msg)
            state = StateExtractor.extract_from_turns([msg])
            res = engine.evaluate_case(
                customer_text=msg,
                intent=intent,
                intent_confidence=conf,
                state=state,
                drift_monitor=drift_monitor
            )
            decisions.append(res['decision'])
            
        metrics = EvaluationMetrics.compute_safety_and_coverage(decisions, gold_decisions, gold_should_escalate)
        sweep_results.append({
            'threshold': thresh,
            'coverage': metrics['coverage'],
            'false_auto_rate': metrics['false_auto_handling_rate'],
            'auto_count': metrics['auto_handled_count'],
            'false_auto_count': metrics['unsafe_auto_count']
        })

    print("=== AUTOMATION SAFETY CURVE THRESHOLD SWEEP (207 CASES) ===")
    for r in sweep_results:
        frozen_mark = " <-- [FROZEN OPERATING POINT]" if r['threshold'] == 0.55 else ""
        print(f"Thresh A >= {r['threshold']:.2f} | Coverage: {r['coverage']:>6.1%} ({r['auto_count']:>3}/{len(df_golden)}) | False Auto: {r['false_auto_rate']:>5.1%} ({r['false_auto_count']:>2} cases){frozen_mark}")

    # Plot curve
    plt.figure(figsize=(9, 6), dpi=200)

    covs = [r['coverage'] * 100 for r in sweep_results]
    false_rates = [r['false_auto_rate'] * 100 for r in sweep_results]

    # Plot curve line
    plt.plot(covs, false_rates, color='#1DB954', linestyle='--', linewidth=2, label='ResolveTrace Threshold Sweep (A in [0.20, 0.80])', zorder=3)
    plt.scatter(covs, false_rates, color='#1DB954', s=60, zorder=4)

    for i, r in enumerate(sweep_results):
        t_val = r['threshold']
        if t_val == 0.55:
            plt.scatter([r['coverage'] * 100], [r['false_auto_rate'] * 100], color='blue', s=180, marker='*', zorder=6, label='Chosen Operating Point (A >= 0.55)')
            plt.annotate(
                f"OPERATING POINT (A >= 0.55)\nCov: {r['coverage']:.1%}, False Auto: {r['false_auto_rate']:.1%}",
                (r['coverage'] * 100, r['false_auto_rate'] * 100),
                textcoords="offset points",
                xytext=(-40, 20),
                fontsize=9,
                fontweight='bold',
                color='blue',
                bbox=dict(boxstyle='round,pad=0.3', edgecolor='blue', facecolor='white', alpha=0.9),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.2', color='blue', lw=1.5)
            )
        else:
            plt.annotate(f"A>={t_val:.2f}", (r['coverage'] * 100, r['false_auto_rate'] * 100), textcoords="offset points", xytext=(5, -12), fontsize=8, color='#333333')

    # Baselines for comparison
    plt.scatter([100.0], [11.8], color='red', s=120, marker='o', label='Semantic RAG (Ungated: 100% Cov / 11.8% False Auto)', zorder=5)
    plt.scatter([100.0], [11.8], color='purple', s=120, marker='^', label='Vanilla Playbook (Ungated: 100% Cov / 11.8% False Auto)', zorder=5)

    plt.xlabel('Automation Coverage (% of cases auto-handled)', fontsize=11, fontweight='bold')
    plt.ylabel('False Auto-Handling Rate (% unsafe auto-handles)', fontsize=11, fontweight='bold')
    plt.title('Automation Safety Curve — Threshold Sweep vs. False Auto-Handling', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.xlim(10, 105)
    plt.ylim(0, 16)
    plt.legend(loc='upper left', fontsize=9)
    plt.tight_layout()

    os.makedirs('artifacts/figures', exist_ok=True)
    out_img = 'artifacts/figures/automation_safety_curve.png'
    plt.savefig(out_img)
    print(f"Safety curve plot saved to {out_img}")

if __name__ == '__main__':
    run_sweep()
