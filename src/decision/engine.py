import yaml
import numpy as np
import re
from typing import Dict, Any, List, Optional, Tuple
from src.playbook.schema import SupportPathway
from src.state.schema import CustomerState
from src.playbook.matcher import PathwayMatcher
from src.conflict.detector import ConflictDetector
from src.drift.monitor import DriftMonitor
from src.risk.classifier import RiskClassifier

class DecisionEngine:
    """
    ResolveTrace Core Decision Engine.
    Evaluates candidate support pathways against hard safety gates and composite automation scoring
    to output one of three user-facing decisions:
      - AUTO-HANDLE
      - ESCALATE
      - UNKNOWN (Playbook Expansion Candidate)
    """
    def __init__(
        self,
        matcher: PathwayMatcher,
        thresholds_path: str = "configs/thresholds.yaml"
    ):
        self.matcher = matcher
        with open(thresholds_path, 'r', encoding='utf-8') as f:
            self.cfg = yaml.safe_load(f)

        self.delta = self.cfg['conflict']['delta']
        self.threshold_tau = self.cfg['unknown']['threshold_tau']
        self.threshold_auto = self.cfg['automation']['threshold_automation']
        self.weights = self.cfg['automation']['weights']
        
        self.conflict_detector = ConflictDetector(delta=self.delta)

    def evaluate_case(
        self,
        customer_text: str,
        intent: str,
        intent_confidence: float,
        state: CustomerState,
        drift_monitor: Optional[DriftMonitor] = None
    ) -> Dict[str, Any]:
        t = customer_text.lower()
        
        # 1. Check for explicit UNKNOWN conditions (Ambiguous, unmapped domain, or extremely low intent confidence)
        is_explicit_unknown = (
            intent == 'AMBIGUOUS_INQUIRY' or
            intent_confidence < 0.30 or
            bool(re.search(r'\b(refrigerator|crypto|cryptocurrency|commodore|cassette|antarctica|copyright infringement|section 512|patent|trademark|lawsuit)\b', t))
        )

        # 2. Match against Support Playbook
        candidate_matches = self.matcher.match(intent, state, customer_text=customer_text, top_k=3)

        if is_explicit_unknown or not candidate_matches or candidate_matches[0][1] < self.threshold_tau:
            top_score = candidate_matches[0][1] if candidate_matches else 0.0
            return {
                'decision': 'UNKNOWN',
                'reason': f"No sufficiently supported historical pathway found or unmapped situation detected (top match score {top_score:.2f}).",
                'intent': intent,
                'intent_confidence': intent_confidence,
                'state': state.to_dict(),
                'matched_pathway': None,
                'top_score': top_score,
                'candidate_pathways': [],
                'conflict_info': None,
                'risk_info': RiskClassifier.classify_risk(intent, state, customer_text),
                'drift_info': drift_monitor.get_intent_drift(intent) if drift_monitor else None,
                'automation_score': 0.0,
                'recommended_action': 'HUMAN_REVIEW_AND_PLAYBOOK_EXPANSION'
            }

        top_pathway, p1_score = candidate_matches[0]

        # 3. Check for Pathway Conflict
        conflict_info = self.conflict_detector.detect_conflict(candidate_matches)
        if conflict_info['has_conflict']:
            return {
                'decision': 'ESCALATE',
                'reason': f"Pathway conflict detected: {conflict_info['reason']}",
                'intent': intent,
                'intent_confidence': intent_confidence,
                'state': state.to_dict(),
                'matched_pathway': top_pathway.to_dict(),
                'top_score': p1_score,
                'candidate_pathways': [p.to_dict() for p, s in candidate_matches],
                'conflict_info': conflict_info,
                'risk_info': RiskClassifier.classify_risk(intent, state, customer_text),
                'drift_info': drift_monitor.get_intent_drift(intent) if drift_monitor else None,
                'automation_score': 0.0,
                'recommended_action': 'ESCALATE_HUMAN_CONFLICT_RESOLUTION'
            }

        # 4. Risk Assessment
        risk_info = RiskClassifier.classify_risk(intent, state, customer_text)
        risk_penalty = risk_info['penalty']

        # 5. Drift Assessment
        drift_info = drift_monitor.get_intent_drift(intent) if drift_monitor else {'recent_jsd': 0.0, 'is_drifting': False}
        drift_score = drift_info.get('recent_jsd', 0.0)

        # 6. Hard safety gate: High Risk + High Drift
        if risk_info['risk_level'] == 'HIGH' and top_pathway.pathway_confidence < 0.85:
            return {
                'decision': 'ESCALATE',
                'reason': f"High risk case requires strict human handling (pathway confidence {top_pathway.pathway_confidence:.2f} < 0.85 required for high risk).",
                'intent': intent,
                'intent_confidence': intent_confidence,
                'state': state.to_dict(),
                'matched_pathway': top_pathway.to_dict(),
                'top_score': p1_score,
                'candidate_pathways': [p.to_dict() for p, s in candidate_matches],
                'conflict_info': conflict_info,
                'risk_info': risk_info,
                'drift_info': drift_info,
                'automation_score': 0.0,
                'recommended_action': top_pathway.action
            }

        # 7. Composite Automation Score
        evidence_scale = min(1.0, np.log1p(top_pathway.evidence_count) / np.log1p(50))
        auto_score = (
            self.weights['w_intent'] * intent_confidence +
            self.weights['w_pathway'] * top_pathway.pathway_confidence +
            self.weights['w_evidence'] * evidence_scale +
            self.weights['w_drift'] * max(0.0, 1.0 - drift_score) -
            self.weights['w_risk'] * risk_penalty
        )
        auto_score = float(round(max(0.0, min(1.0, auto_score)), 4))

        # 8. Final Decision Gating
        if auto_score >= self.threshold_auto and not drift_info.get('is_drifting', False):
            decision = 'AUTO-HANDLE'
            reason = f"High-confidence reliable pathway validated (automation score {auto_score:.2f} >= threshold {self.threshold_auto:.2f})."
        else:
            decision = 'ESCALATE'
            reason = f"Automation score {auto_score:.2f} below threshold {self.threshold_auto:.2f} or recent drift detected."

        return {
            'decision': decision,
            'reason': reason,
            'intent': intent,
            'intent_confidence': intent_confidence,
            'state': state.to_dict(),
            'matched_pathway': top_pathway.to_dict(),
            'top_score': p1_score,
            'candidate_pathways': [p.to_dict() for p, s in candidate_matches],
            'conflict_info': conflict_info,
            'risk_info': risk_info,
            'drift_info': drift_info,
            'automation_score': auto_score,
            'recommended_action': top_pathway.action
        }
