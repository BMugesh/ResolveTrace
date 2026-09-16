import unittest
import os
import json
from src.generation.grounded_generator import GroundedResponseGenerator
from src.state.schema import CustomerState
from src.playbook.schema import SupportPathway

class TestGroundedResponseGenerator(unittest.TestCase):
    def setUp(self):
        self.state = CustomerState(
            info_provided=True,
            troubleshoot_attempted=False,
            issue_recurring=False,
            billing_related=False,
            device_type='iPhone'
        )
        self.pathway = {
            'pathway_id': 'PW_TEST_001',
            'intent': 'OFFLINE_SYNC_DOWNLOADS',
            'action': 'PROVIDE_INSTRUCTIONS',
            'sample_agent_responses': [
                '@12345 Hey Sarah! To clear offline cache on iPhone: open Spotify > Settings > Storage > Clear Cache. /TF'
            ]
        }

    def test_pre_call_sanitization(self):
        raw_snippet = "@12345 Hey Sarah! Clear cache in Settings /TF"
        sanitized = GroundedResponseGenerator.sanitize_text(raw_snippet)
        self.assertNotIn("@12345", sanitized)
        self.assertNotIn("Sarah", sanitized)
        self.assertNotIn("/TF", sanitized)
        self.assertTrue(sanitized.startswith("Hey there!"))

    def test_prompt_construction(self):
        res = GroundedResponseGenerator.generate(
            intent='OFFLINE_SYNC_DOWNLOADS',
            state=self.state,
            action='PROVIDE_INSTRUCTIONS',
            customer_text='@SpotifyCares How do I clear offline cache on iPhone?',
            matched_pathway=self.pathway,
            decision='AUTO-HANDLE',
            return_full_result=True
        )
        self.assertIn("You are drafting a SpotifyCares support reply.", res['prompt'])
        self.assertIn("Customer message: How do I clear offline cache on iPhone?", res['prompt'])
        self.assertNotIn("@SpotifyCares", res['prompt'])
        self.assertIn("OFFLINE_SYNC_DOWNLOADS", res['prompt'])
        self.assertIn("PROVIDE_INSTRUCTIONS", res['prompt'])
        self.assertEqual(res['status'], 'SUCCESS')
        self.assertFalse(res['fallback_escalate'])

    def test_skip_generation_for_non_auto_handle(self):
        res_esc = GroundedResponseGenerator.generate(
            intent='ACCOUNT_ACCESS_AUTH',
            state=self.state,
            action='REDIRECT_DM',
            customer_text='Someone compromised my account!',
            decision='ESCALATE',
            return_full_result=True
        )
        self.assertEqual(res_esc['status'], 'SKIPPED_FOR_NON_AUTO_HANDLE')
        self.assertIsNone(res_esc['reply'])

        res_unk = GroundedResponseGenerator.generate(
            intent='GENERAL_INQUIRY_FEEDBACK',
            state=self.state,
            action='PROVIDE_GENERAL_ASSISTANCE',
            customer_text='Can I install Spotify on a smart microwave?',
            decision='UNKNOWN',
            return_full_result=True
        )
        self.assertEqual(res_unk['status'], 'SKIPPED_FOR_NON_AUTO_HANDLE')
        self.assertIsNone(res_unk['reply'])

    def test_generate_accepts_matched_pathway_and_customer_text(self):
        matched = {
            'sample_agent_responses': [
                'Hey there! Can you let us know what happens when downloads stop?'
            ]
        }
        res = GroundedResponseGenerator.generate(
            intent='OFFLINE_SYNC_DOWNLOADS',
            state=CustomerState(device_type='Mobile/Phone'),
            action='REQUEST_INFORMATION',
            matched_pathway=matched,
            customer_text='my songs stop downloading even after restarting my phone',
            return_full_result=True
        )

        self.assertIn(
            'Customer message: my songs stop downloading even after restarting my phone',
            res['prompt']
        )

    def test_artifact_logging(self):
        GroundedResponseGenerator.generate(
            intent='OFFLINE_SYNC_DOWNLOADS',
            state=self.state,
            action='PROVIDE_INSTRUCTIONS',
            customer_text='@SpotifyCares How do I re-download songs?',
            matched_pathway=self.pathway,
            decision='AUTO-HANDLE',
            return_full_result=True
        )
        self.assertTrue(os.path.exists('artifacts/generation_logs.jsonl'))
        with open('artifacts/generation_logs.jsonl', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        self.assertGreater(len(lines), 0)
        latest = json.loads(lines[-1])
        self.assertIn('prompt', latest)
        self.assertIn('judge_scores', latest)

    def test_escalate_and_unknown_never_return_customer_facing_draft(self):
        """
        Safety invariant: An ESCALATE or UNKNOWN decision must never produce
        an autonomous customer-facing reply draft. It must strictly return
        the human routing supervisor audit tag.
        """
        # 1. Test ESCALATE string return
        reply_esc = GroundedResponseGenerator.generate(
            intent='ACCOUNT_ACCESS_AUTH',
            state=self.state,
            action='REDIRECT_DM',
            matched_pathway=self.pathway,
            customer_text='Someone hacked my account!',
            decision='ESCALATE'
        )
        self.assertTrue(reply_esc.startswith("[ESCALATE:"))
        self.assertIn("Case routed to human specialist / queue", reply_esc)
        self.assertNotIn("/SC", reply_esc)
        self.assertNotIn("https://", reply_esc)
        self.assertNotIn("Hey there", reply_esc)

        # 2. Test UNKNOWN string return
        reply_unk = GroundedResponseGenerator.generate(
            intent='GENERAL_INQUIRY_FEEDBACK',
            state=self.state,
            action='PROVIDE_GENERAL_ASSISTANCE',
            matched_pathway=self.pathway,
            customer_text='Can I install Spotify on a smart microwave?',
            decision='UNKNOWN'
        )
        self.assertTrue(reply_unk.startswith("[UNKNOWN:"))
        self.assertIn("Case routed to human specialist / queue", reply_unk)
        self.assertNotIn("/SC", reply_unk)
        self.assertNotIn("https://", reply_unk)
        self.assertNotIn("Hey there", reply_unk)

if __name__ == '__main__':
    unittest.main()
