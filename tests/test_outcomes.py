import unittest
from src.resolution.outcomes import OutcomeInferenceEngine

class TestOutcomeInference(unittest.TestCase):
    def test_explicit_resolved(self):
        turns = [
            {'author_type': 'customer', 'text': 'My playlist won\'t play.'},
            {'author_type': 'support', 'author_id': 'SpotifyCares', 'text': 'Try logging out and logging back in.'},
            {'author_type': 'customer', 'text': 'Brilliant thanks that fixed it completely!'}
        ]
        outcome, evidence, conf = OutcomeInferenceEngine.infer_outcome(turns)
        self.assertEqual(outcome, 'RESOLVED')
        self.assertGreaterEqual(conf, 0.90)

    def test_likely_resolved(self):
        turns = [
            {'author_type': 'customer', 'text': 'How do I download offline music?'},
            {'author_type': 'support', 'author_id': 'SpotifyCares', 'text': 'Tap the download toggle at the top of the playlist.'},
            {'author_type': 'customer', 'text': 'Got it thanks!'}
        ]
        outcome, evidence, conf = OutcomeInferenceEngine.infer_outcome(turns)
        self.assertEqual(outcome, 'LIKELY_RESOLVED')

    def test_escalated_to_dm(self):
        turns = [
            {'author_type': 'customer', 'text': 'Someone changed my email address.'},
            {'author_type': 'support', 'author_id': 'SpotifyCares', 'text': 'Please send us a DM with your details so we can investigate backstage: https://t.co/ldFdZRiNAt'}
        ]
        outcome, evidence, conf = OutcomeInferenceEngine.infer_outcome(turns)
        self.assertEqual(outcome, 'ESCALATED')

    def test_unresolved_open(self):
        turns = [
            {'author_type': 'customer', 'text': 'Spotify is slow.'},
            {'author_type': 'support', 'author_id': 'SpotifyCares', 'text': 'What version are you using?'}
        ]
        outcome, evidence, conf = OutcomeInferenceEngine.infer_outcome(turns)
        self.assertEqual(outcome, 'UNRESOLVED_OPEN')

if __name__ == '__main__':
    unittest.main()
