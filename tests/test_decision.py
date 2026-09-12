import unittest
from src.playbook.schema import SupportPathway
from src.playbook.matcher import PathwayMatcher
from src.decision.engine import DecisionEngine
from src.state.schema import CustomerState

class TestDecisionEngine(unittest.TestCase):
    def setUp(self):
        p1 = SupportPathway(
            pathway_id="PW_SAFE_001",
            intent="PLAYBACK_STREAMING_AUDIO",
            conditions={'info_provided': True, 'troubleshoot_attempted': False, 'issue_recurring': False, 'billing_related': False, 'device_type': 'Android'},
            action="PROVIDE_INSTRUCTIONS",
            outcome_distribution={'RESOLVED': 80, 'LIKELY_RESOLVED': 20},
            evidence_count=100,
            recent_evidence_count=30,
            pathway_confidence=0.92,
            last_observed="2017-11-01",
            status="ACTIVE"
        )
        self.matcher = PathwayMatcher([p1])
        self.engine = DecisionEngine(self.matcher, thresholds_path="configs/thresholds.yaml")

    def test_safe_auto_handle(self):
        state = CustomerState(info_provided=True, troubleshoot_attempted=False, issue_recurring=False, billing_related=False, device_type='Android')
        msg = "My music stopped playing on Android."
        res = self.engine.evaluate_case(msg, "PLAYBACK_STREAMING_AUDIO", 0.95, state)
        self.assertEqual(res['decision'], 'AUTO-HANDLE')
        self.assertEqual(res['recommended_action'], 'PROVIDE_INSTRUCTIONS')

    def test_unknown_case(self):
        state = CustomerState(info_provided=True, troubleshoot_attempted=False, issue_recurring=False, billing_related=False, device_type='unknown')
        msg = "Can I install Spotify on my refrigerator in Korean?"
        res = self.engine.evaluate_case(msg, "GENERAL_INQUIRY_FEEDBACK", 0.20, state)
        self.assertEqual(res['decision'], 'UNKNOWN')

if __name__ == '__main__':
    unittest.main()
