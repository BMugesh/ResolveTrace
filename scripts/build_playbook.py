import os
import sys
import json
import time
import yaml
import pandas as pd
from collections import Counter

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data.loader import ConversationLoader
from src.playbook.builder import PlaybookBuilder
from src.playbook.store import PlaybookStore
from src.resolution.audit import PlaybookAuditor
from src.drift.monitor import DriftMonitor

def build_playbook():
    start_time = time.time()
    print("=" * 70)
    print("BUILDING SPOTIFYCARES HISTORICAL SUPPORT PLAYBOOK")
    print("=" * 70)

    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('configs/thresholds.yaml', 'r') as f:
        thresholds = yaml.safe_load(f)

    train_path = config['paths']['train_conversations_jsonl']
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"Train split not found at {train_path}. Run scripts/build_dataset.py first.")

    print(f"Loading training conversations from {train_path}...")
    train_convs = ConversationLoader.load_jsonl(train_path)
    print(f"Loaded {len(train_convs):,} training conversations.")

    # 1. Mine Pathways
    print("\nMining decision pathways with Bayesian Laplace confidence shrinkage...")
    builder = PlaybookBuilder(
        min_evidence=thresholds['pathway']['minimum_evidence'],
        min_confidence=thresholds['pathway']['minimum_confidence'],
        laplace_prior_weight=thresholds['pathway']['laplace_prior_weight'],
        base_success_prior=thresholds['pathway']['base_success_prior']
    )
    pathways = builder.build_from_conversations(train_convs)
    print(f"Mined {len(pathways):,} total support pathways.")

    active_pws = [p for p in pathways if p.status == 'ACTIVE']
    probation_pws = [p for p in pathways if p.status == 'PROBATION']
    sparse_pws = [p for p in pathways if p.status == 'SPARSE']
    print(f"  ACTIVE Pathways (>= {thresholds['pathway']['minimum_evidence']} evidence, >= {thresholds['pathway']['minimum_confidence']} conf): {len(active_pws)}")
    print(f"  PROBATION Pathways (>= {thresholds['pathway']['minimum_evidence']} evidence, < {thresholds['pathway']['minimum_confidence']} conf): {len(probation_pws)}")
    print(f"  SPARSE Pathways (< {thresholds['pathway']['minimum_evidence']} evidence): {len(sparse_pws)}")

    # 2. Save Playbook
    playbook_path = config['paths']['playbook_json']
    store = PlaybookStore(playbook_path)
    store.save(pathways)
    print(f"\nSaved Support Playbook to {playbook_path}")

    # 3. Audit Playbook
    print("\nAuditing Support Playbook...")
    audit_results = PlaybookAuditor.audit_pathways([p.to_dict() for p in pathways])
    print(f"  Schema Validity Rate: {audit_results['schema_validity_rate']:.1%}")
    print(f"  Vocabulary Validity Rate: {audit_results['vocabulary_validity_rate']:.1%}")
    print(f"  Evidence Grounding Rate: {audit_results['evidence_grounding_rate']:.1%}")
    print(f"  Outliers Identified: {audit_results['outlier_count']}")

    # 4. Audit Outcome Inference Sample
    print("\nAuditing Outcome Inference on sample...")
    outcome_audit = PlaybookAuditor.audit_outcome_sample(train_convs, sample_size=100)
    print(f"  Audit Sample Size: {outcome_audit['audit_sample_size']}")
    print(f"  Sample Outcome Distribution: {outcome_audit['outcome_distribution']}")

    # 5. Save Pathway Metrics
    pathway_metrics = {
        'total_pathways': len(pathways),
        'active_pathways': len(active_pws),
        'probation_pathways': len(probation_pws),
        'sparse_pathways': len(sparse_pws),
        'audit_results': audit_results,
        'outcome_audit': outcome_audit,
        'top_15_active_pathways': [
            {
                'id': p.pathway_id,
                'intent': p.intent,
                'action': p.action,
                'conditions': p.conditions,
                'evidence_count': p.evidence_count,
                'confidence': p.pathway_confidence,
                'status': p.status
            } for p in active_pws[:15]
        ]
    }

    metrics_path = config['paths']['pathway_metrics_json']
    with open(metrics_path, 'w') as f:
        json.dump(pathway_metrics, f, indent=2)
    print(f"Saved pathway metrics to {metrics_path}")

    print(f"\nPlaybook construction completed in {time.time() - start_time:.2f}s")

if __name__ == '__main__':
    build_playbook()
