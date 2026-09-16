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

    @staticmethod
    def compute_significance_mcnemar(rt_correct: List[bool], rag_correct: List[bool]) -> Dict[str, Any]:
        """
        Computes exact McNemar paired test and Edwards chi-squared test between ResolveTrace and Semantic RAG.
        """
        from scipy import stats
        a = sum(1 for r, t in zip(rag_correct, rt_correct) if r and t)
        b = sum(1 for r, t in zip(rag_correct, rt_correct) if r and not t)
        c = sum(1 for r, t in zip(rag_correct, rt_correct) if not r and t)
        d = sum(1 for r, t in zip(rag_correct, rt_correct) if not r and not t)
        
        discordant = b + c
        if discordant == 0:
            return {
                'both_correct': a,
                'rag_only_correct': b,
                'rt_only_correct': c,
                'both_incorrect': d,
                'discordant_pairs': 0,
                'exact_p_value': 1.0,
                'chi2_stat': 0.0,
                'chi2_p_value': 1.0,
                'p_value_display': "p = 1.000"
            }

        binom_res = stats.binomtest(b, discordant, p=0.5, alternative='two-sided')
        exact_p = float(binom_res.pvalue)

        chi2_corr = ((abs(b - c) - 1) ** 2) / discordant
        p_corr = float(stats.chi2.sf(chi2_corr, df=1))

        p_display = f"p = {exact_p:.4f}" if exact_p < 0.01 else f"p = {exact_p:.3f}"

        return {
            'both_correct': a,
            'rag_only_correct': b,
            'rt_only_correct': c,
            'both_incorrect': d,
            'contingency_table': [[a, b], [c, d]],
            'discordant_pairs': discordant,
            'exact_p_value': float(round(exact_p, 6)),
            'chi2_stat': float(round(chi2_corr, 4)),
            'chi2_p_value': float(round(p_corr, 6)),
            'p_value_display': p_display
        }
