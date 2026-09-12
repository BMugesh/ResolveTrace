import unittest
from src.drift.jsd import compute_jsd
from src.drift.monitor import DriftMonitor

class TestDriftCalculation(unittest.TestCase):
    def test_identical_distributions_zero_jsd(self):
        dist_a = {'PROVIDE_INSTRUCTIONS': 0.8, 'REDIRECT_DM': 0.2}
        dist_b = {'PROVIDE_INSTRUCTIONS': 0.8, 'REDIRECT_DM': 0.2}
        jsd = compute_jsd(dist_a, dist_b)
        self.assertAlmostEqual(jsd, 0.0, places=3)

    def test_divergent_distributions_high_jsd(self):
        dist_a = {'PROVIDE_INSTRUCTIONS': 1.0, 'REDIRECT_DM': 0.0}
        dist_b = {'PROVIDE_INSTRUCTIONS': 0.0, 'REDIRECT_DM': 1.0}
        jsd = compute_jsd(dist_a, dist_b)
        self.assertGreater(jsd, 0.80)

    def test_drift_monitor_fit(self):
        records = [
            {'intent': 'TEST_INTENT', 'action': 'PROVIDE_INSTRUCTIONS'},
            {'intent': 'TEST_INTENT', 'action': 'PROVIDE_INSTRUCTIONS'},
            {'intent': 'TEST_INTENT', 'action': 'REDIRECT_DM'},
            {'intent': 'TEST_INTENT', 'action': 'REDIRECT_DM'}
        ] * 10
        monitor = DriftMonitor(num_windows=2, min_samples_per_window=2)
        monitor.fit_from_records(records)
        res = monitor.get_intent_drift('TEST_INTENT')
        self.assertIn('recent_jsd', res)
        self.assertFalse(res['is_drifting'])

if __name__ == '__main__':
    unittest.main()
