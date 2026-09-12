import unittest
from src.playbook.schema import SupportPathway
from src.playbook.matcher import PathwayMatcher
from src.state.schema import CustomerState

class TestPathwayMatcher(unittest.TestCase):
    def setUp(self):
        self.p1 = SupportPathway(
            pathway_id="PW_TEST_001",
            intent="PLAYBACK_STREAMING_AUDIO",
            conditions={'info_provided': True, 'troubleshoot_attempted': False, 'issue_recurring': True, 'billing_related': False, 'device_type': 'Android'},
            action="TROUBLESHOOT_RESTART",
            outcome_distribution={'RESOLVED': 10, 'UNRESOLVED_OPEN': 2},
            evidence_count=12,
            recent_evidence_count=4,
            pathway_confidence=0.85,
            last_observed="2017-11-01",
            status="ACTIVE"
        )
        self.p2 = SupportPathway(
            pathway_id="PW_TEST_002",
            intent="SUBSCRIPTION_BILLING_PREMIUM",
            conditions={'info_provided': True, 'troubleshoot_attempted': False, 'issue_recurring': False, 'billing_related': True, 'device_type': 'unknown'},
            action="REDIRECT_DM",
            outcome_distribution={'ESCALATED': 50},
            evidence_count=50,
            recent_evidence_count=15,
            pathway_confidence=0.90,
            last_observed="2017-11-01",
            status="ACTIVE"
        )
        self.matcher = PathwayMatcher([self.p1, self.p2])

    def test_strong_match(self):
        state = CustomerState(info_provided=True, troubleshoot_attempted=False, issue_recurring=True, billing_related=False, device_type='Android')
        matches = self.matcher.match('PLAYBACK_STREAMING_AUDIO', state, top_k=1)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].pathway_id, 'PW_TEST_001')
        self.assertGreater(matches[0][1], 0.55)

    def test_intent_mismatch_zero_score(self):
        state = CustomerState(info_provided=True, troubleshoot_attempted=False, issue_recurring=True, billing_related=False, device_type='Android')
        matches = self.matcher.match('ACCOUNT_ACCESS_AUTH', state, top_k=1)
        self.assertEqual(len(matches), 0)

if __name__ == '__main__':
    unittest.main()
