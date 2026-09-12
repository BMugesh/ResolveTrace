from typing import List, Tuple, Dict, Any, Optional
from src.playbook.schema import SupportPathway

class ConflictDetector:
    """
    Detects competing/conflicting support pathways when a customer case matches multiple
    candidate pathways with nearly identical confidence scores recommending opposing support strategies.
    """
    ACTION_FAMILIES = {
        'REQUEST_INFO_AND_REDIRECT_DM': 'DM_ROUTING',
        'REDIRECT_DM': 'DM_ROUTING',
        'PROVIDE_INSTRUCTIONS': 'SELF_SERVE',
        'EXPLAIN_POLICY_OR_CATALOG': 'SELF_SERVE',
        'TROUBLESHOOT_REINSTALL': 'TECHNICAL_TROUBLESHOOT',
        'TROUBLESHOOT_UPDATE': 'TECHNICAL_TROUBLESHOOT',
        'TROUBLESHOOT_RESTART': 'TECHNICAL_TROUBLESHOOT',
        'REQUEST_INFORMATION': 'DIAGNOSTIC_PROBING',
        'ESCALATE_INTERNAL': 'INTERNAL_ESCALATION',
        'CONFIRM_RESOLUTION': 'RESOLUTION_CONFIRMATION',
        'CLOSING_COURTESY': 'RESOLUTION_CONFIRMATION',
        'PROVIDE_GENERAL_ASSISTANCE': 'GENERAL_SUPPORT'
    }

    def __init__(self, delta: float = 0.12):
        self.delta = delta

    def detect_conflict(self, candidate_matches: List[Tuple[SupportPathway, float]]) -> Dict[str, Any]:
        """
        If top pathway P1 and second pathway P2 recommend fundamentally different action families
        and (P1_score - P2_score) < delta, flag an operational CONFLICT.
        """
        if len(candidate_matches) < 2:
            return {
                'has_conflict': False,
                'delta': self.delta,
                'score_difference': None,
                'competing_actions': []
            }

        p1, s1 = candidate_matches[0]
        p2, s2 = candidate_matches[1]
        score_diff = float(round(s1 - s2, 4))

        family1 = self.ACTION_FAMILIES.get(p1.action, p1.action)
        family2 = self.ACTION_FAMILIES.get(p2.action, p2.action)

        # Conflict exists only if action families differ and scores are close
        if family1 != family2 and score_diff < self.delta:
            return {
                'has_conflict': True,
                'delta': self.delta,
                'score_difference': score_diff,
                'top_pathway_id': p1.pathway_id,
                'top_action': p1.action,
                'second_pathway_id': p2.pathway_id,
                'second_action': p2.action,
                'competing_actions': [p1.action, p2.action],
                'reason': f"Top pathway strategy '{p1.action}' ({family1}, score {s1:.2f}) closely conflicts with '{p2.action}' ({family2}, score {s2:.2f}, diff {score_diff:.2f} < delta {self.delta:.2f})"
            }

        return {
            'has_conflict': False,
            'delta': self.delta,
            'score_difference': score_diff,
            'competing_actions': [p1.action]
        }
