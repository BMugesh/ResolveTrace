import unittest
from src.state.extractor import StateExtractor

class TestStateExtraction(unittest.TestCase):
    def test_state_extraction_known_device_and_troubleshooting(self):
        text = "I have an iPhone 7 running iOS 11.1 and I've already restarted my phone and reinstalled the app but it still crashes."
        state = StateExtractor.extract_from_turns([text])

        self.assertEqual(state.device_type, 'iPhone')
        self.assertTrue(state.os_version_provided)
        self.assertTrue(state.troubleshoot_attempted)
        self.assertTrue(state.issue_recurring)
        self.assertFalse(state.billing_related)
        self.assertTrue(state.info_provided)
        self.assertIn('device_type', state.evidence)

    def test_state_extraction_billing_and_unknown_device(self):
        text = "Why was I charged twice on my credit card this month? Please refund my $9.99 payment."
        state = StateExtractor.extract_from_turns([text])

        self.assertEqual(state.device_type, 'unknown')
        self.assertTrue(state.billing_related)
        self.assertFalse(state.troubleshoot_attempted)
        self.assertIn('billing_related', state.evidence)

    def test_ambiguous_sparse_text(self):
        text = "@SpotifyCares help"
        state = StateExtractor.extract_from_turns([text])
        self.assertTrue(state.is_ambiguous)

if __name__ == '__main__':
    unittest.main()
