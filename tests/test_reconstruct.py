import unittest
import pandas as pd
import numpy as np
from src.data.reconstruct import ConversationReconstructor

class TestConversationReconstruction(unittest.TestCase):
    def setUp(self):
        self.reconstructor = ConversationReconstructor(brand_name="SpotifyCares")

    def test_basic_thread_reconstruction(self):
        # Construct synthetic dataframe
        data = {
            'tweet_id': [1, 2, 3],
            'author_id': ['1001', 'SpotifyCares', '1001'],
            'inbound': [True, False, True],
            'created_at': ['Wed Oct 11 10:00:00 +0000 2017', 'Wed Oct 11 10:05:00 +0000 2017', 'Wed Oct 11 10:10:00 +0000 2017'],
            'text': ['My music stopped playing', 'Hi! What device are you on?', 'Android 8.0 on Galaxy S8'],
            'response_tweet_id': ['2', '3', ''],
            'in_response_to_tweet_id': [np.nan, 1, 2]
        }
        df = pd.DataFrame(data)
        convs, indices = self.reconstructor.reconstruct_from_dataframe(df)

        self.assertEqual(len(convs), 1)
        conv = convs[0]
        self.assertEqual(conv['root_tweet_id'], 1)
        self.assertEqual(conv['num_turns'], 3)
        self.assertEqual(conv['turns'][0]['author_type'], 'customer')
        self.assertEqual(conv['turns'][1]['author_type'], 'support')
        self.assertEqual(conv['turns'][2]['author_type'], 'customer')

    def test_broken_chain_discarded(self):
        # Brand replies to a tweet that does not exist in the dataset
        data = {
            'tweet_id': [10],
            'author_id': ['SpotifyCares'],
            'inbound': [False],
            'created_at': ['Wed Oct 11 10:00:00 +0000 2017'],
            'text': ['Send us a DM!'],
            'response_tweet_id': [''],
            'in_response_to_tweet_id': [999] # Missing root
        }
        df = pd.DataFrame(data)
        convs, _ = self.reconstructor.reconstruct_from_dataframe(df)
        self.assertEqual(len(convs), 0)

if __name__ == '__main__':
    unittest.main()
