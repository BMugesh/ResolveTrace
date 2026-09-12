import unittest
from src.playbook.schema import SupportPathway
from src.conflict.detector import ConflictDetector

class TestConflictDetector(unittest.TestCase):
    def setUp(self):
        self.detector = ConflictDetector(delta=0.08)

    def test_conflict_between_different_action_families(self):
        p1 = SupportPathway(
            pathway_id="PW_1", intent="APP_CRASH_BUG", conditions={}, action="PROVIDE_INSTRUCTIONS",
            outcome_distribution={}, evidence_count=10, recent_evidence_count=3, pathway_confidence=0.85, last_observed="2017", status="ACTIVE"
        )
        p2 = SupportPathway(
            pathway_id="PW_2", intent="APP_CRASH_BUG", conditions={}, action="REDIRECT_DM",
            outcome_distribution={}, evidence_count=10, recent_evidence_count=3, pathway_confidence=0.84, last_observed="2017", status="ACTIVE"
        )
        # Match scores: 0.85 and 0.83 (diff = 0.02 < delta 0.08)
        candidate_matches = [(p1, 0.85), (p2, 0.83)]
        res = self.detector.detect_conflict(candidate_matches)
        self.assertTrue(res['has_conflict'])
        self.assertEqual(res['score_difference'], 0.02)

    def test_no_conflict_when_same_action_family(self):
        p1 = SupportPathway(
            pathway_id="PW_1", intent="APP_CRASH_BUG", conditions={}, action="REQUEST_INFO_AND_REDIRECT_DM",
            outcome_distribution={}, evidence_count=10, recent_evidence_count=3, pathway_confidence=0.85, last_observed="2017", status="ACTIVE"
        )
        p2 = SupportPathway(
            pathway_id="PW_2", intent="APP_CRASH_BUG", conditions={}, action="REDIRECT_DM",
            outcome_distribution={}, evidence_count=10, recent_evidence_count=3, pathway_confidence=0.84, last_observed="2017", status="ACTIVE"
        )
        # Both are DM_ROUTING family
        candidate_matches = [(p1, 0.85), (p2, 0.84)]
        res = self.detector.detect_conflict(candidate_matches)
        self.assertFalse(res['has_conflict'])

    def test_no_conflict_when_score_diff_large(self):
        p1 = SupportPathway(
            pathway_id="PW_1", intent="APP_CRASH_BUG", conditions={}, action="PROVIDE_INSTRUCTIONS",
            outcome_distribution={}, evidence_count=50, recent_evidence_count=10, pathway_confidence=0.90, last_observed="2017", status="ACTIVE"
        )
        p2 = SupportPathway(
            pathway_id="PW_2", intent="APP_CRASH_BUG", conditions={}, action="REDIRECT_DM",
            outcome_distribution={}, evidence_count=5, recent_evidence_count=1, pathway_confidence=0.60, last_observed="2017", status="ACTIVE"
        )
        # Diff = 0.20 >= delta 0.08
        candidate_matches = [(p1, 0.85), (p2, 0.65)]
        res = self.detector.detect_conflict(candidate_matches)
        self.assertFalse(res['has_conflict'])

if __name__ == '__main__':
    unittest.main()
