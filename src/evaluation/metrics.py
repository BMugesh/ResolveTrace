import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

class EvaluationMetrics:
    """
    Computes all standard benchmarking metrics for ResolveTrace and baselines.
    """
    @staticmethod
    def compute_pathway_accuracy(pred_actions: List[str], expected_actions: List[str]) -> float:
        if not pred_actions:
            return 0.0
        matches = sum(1 for p, e in zip(pred_actions, expected_actions) if p == e)
        return float(round(matches / len(pred_actions), 4))

    @staticmethod
    def compute_unknown_metrics(pred_decisions: List[str], gold_decisions: List[str]) -> Dict[str, float]:
        y_true = [1 if d == 'UNKNOWN' else 0 for d in gold_decisions]
        y_pred = [1 if d == 'UNKNOWN' else 0 for d in pred_decisions]
        
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
        return {
            'unknown_precision': float(round(p, 4)),
            'unknown_recall': float(round(r, 4)),
            'unknown_f1': float(round(f1, 4))
        }

    @staticmethod
    def compute_conflict_metrics(pred_conflicts: List[bool], gold_conflicts: List[bool]) -> Dict[str, float]:
        y_true = [1 if c else 0 for c in gold_conflicts]
        y_pred = [1 if c else 0 for c in pred_conflicts]
        
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', zero_division=0)
        return {
            'conflict_precision': float(round(p, 4)),
            'conflict_recall': float(round(r, 4)),
            'conflict_f1': float(round(f1, 4))
        }

    @staticmethod
    def compute_safety_and_coverage(pred_decisions: List[str], gold_decisions: List[str], should_escalate_flags: List[bool]) -> Dict[str, float]:
        total = len(pred_decisions)
        if total == 0:
            return {'coverage': 0.0, 'false_auto_handling_rate': 0.0}

        auto_handled_count = sum(1 for d in pred_decisions if d == 'AUTO-HANDLE')
        coverage = auto_handled_count / total

        # False auto-handling occurs when system decides AUTO-HANDLE but case should have been ESCALATED or UNKNOWN
        unsafe_auto_count = sum(
            1 for p_dec, should_esc in zip(pred_decisions, should_escalate_flags)
            if p_dec == 'AUTO-HANDLE' and should_esc
        )
        false_auto_rate = (unsafe_auto_count / auto_handled_count) if auto_handled_count > 0 else 0.0

        return {
            'coverage': float(round(coverage, 4)),
            'false_auto_handling_rate': float(round(false_auto_rate, 4)),
            'auto_handled_count': auto_handled_count,
            'unsafe_auto_count': unsafe_auto_count,
            'total_cases': total
        }
