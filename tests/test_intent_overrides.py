import unittest

from src.classification.tfidf_classifier import TfidfIntentClassifier


class TestIntentOverrides(unittest.TestCase):
    def test_offline_download_mobile_issue_override(self):
        text = (
            "my songs stop downloading for some reason. It just got stuck at a song "
            "and doesn't download at all even when i restarted the app AND my phone"
        )
        self.assertEqual(
            TfidfIntentClassifier._high_precision_intent_override(text),
            'OFFLINE_SYNC_DOWNLOADS'
        )

    def test_general_playback_has_no_override(self):
        self.assertEqual(
            TfidfIntentClassifier._high_precision_intent_override(
                "my music keeps skipping on desktop"
            ),
            ''
        )


if __name__ == '__main__':
    unittest.main()
