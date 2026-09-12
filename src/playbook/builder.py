import json
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
from src.playbook.schema import SupportPathway
from src.taxonomy.discover import RuleBasedIntentClassifier
from src.state.extractor import StateExtractor
from src.resolution.actions import AgentActionExtractor
from src.resolution.outcomes import OutcomeInferenceEngine

class PlaybookBuilder:
    """
    Constructs the Support Playbook by aggregating repeated historical support pathways.
    Applies empirical Bayesian Laplace shrinkage to calculate honest pathway confidence.
    """
    def __init__(
        self,
        min_evidence: int = 5,
        min_confidence: float = 0.60,
        laplace_prior_weight: float = 3.0,
        base_success_prior: float = 0.50
    ):
        self.min_evidence = min_evidence
        self.min_confidence = min_confidence
        self.laplace_prior_weight = laplace_prior_weight
        self.base_success_prior = base_success_prior

    def build_from_conversations(self, conversations: List[Dict[str, Any]]) -> List[SupportPathway]:
        # Group observations by: (intent, conditions_tuple, action)
        pathway_groups = defaultdict(lambda: {
            'outcomes': Counter(),
            'conversations': set(),
            'customer_queries': [],
            'agent_responses': [],
            'timestamps': [],
            'conditions_dict': {}
        })

        for conv in conversations:
            conv_id = conv['conversation_id']
            turns = conv['turns']
            if not turns:
                continue

            # Conversation-level outcome
            outcome, _, _ = OutcomeInferenceEngine.infer_outcome(turns)

            # Customer opening messages
            cust_turns = [t for t in turns if t.get('inbound') or t.get('author_type') == 'customer']
            if not cust_turns:
                continue
            opening_text = cust_turns[0]['text']
            intent = RuleBasedIntentClassifier.classify(opening_text)

            # Process each agent turn
            cum_cust_texts = []
            cum_agent_texts = []
            turn_idx = 0

            for t in turns:
                if t.get('inbound') or t.get('author_type') == 'customer':
                    cum_cust_texts.append(t['text'])
                elif not t.get('inbound') and (t.get('author_id') == 'SpotifyCares' or t.get('author_type') == 'support'):
                    turn_idx += 1
                    agent_text = t['text']
                    timestamp = t.get('timestamp', '')

                    # Extract State
                    state = StateExtractor.extract_from_turns(cum_cust_texts, cum_agent_texts, turn_index=turn_idx)
                    cond_tuple = state.get_condition_tuple()

                    # Extract Action
                    action_data = AgentActionExtractor.extract_action(agent_text)
                    action_name = action_data['action']

                    # Key
                    group_key = (intent, cond_tuple, action_name)
                    pathway_groups[group_key]['outcomes'][outcome] += 1
                    pathway_groups[group_key]['conversations'].add(conv_id)
                    if opening_text and len(pathway_groups[group_key]['customer_queries']) < 8:
                        pathway_groups[group_key]['customer_queries'].append(opening_text)
                    if len(pathway_groups[group_key]['agent_responses']) < 5:
                        pathway_groups[group_key]['agent_responses'].append(agent_text)
                    pathway_groups[group_key]['timestamps'].append(timestamp)
                    pathway_groups[group_key]['conditions_dict'] = {
                        'info_provided': state.info_provided,
                        'troubleshoot_attempted': state.troubleshoot_attempted,
                        'issue_recurring': state.issue_recurring,
                        'billing_related': state.billing_related,
                        'device_type': state.device_type
                    }

                    cum_agent_texts.append(agent_text)

        # Convert groups to SupportPathway objects with Bayesian Confidence
        pathways = []
        pathway_counter = 1

        for (intent, cond_tuple, action_name), data in pathway_groups.items():
            evidence_count = sum(data['outcomes'].values())
            outcomes = dict(data['outcomes'])

            # Empirical success weighting: RESOLVED=1.0, LIKELY_RESOLVED=0.8, ESCALATED=0.7, UNRESOLVED_OPEN=0.2
            effective_successes = (
                outcomes.get('RESOLVED', 0) * 1.0 +
                outcomes.get('LIKELY_RESOLVED', 0) * 0.8 +
                outcomes.get('ESCALATED', 0) * 0.7 +
                outcomes.get('UNRESOLVED_OPEN', 0) * 0.2
            )

            # Bayesian Laplace Shrinkage:
            # Confidence = (Successes + Prior_Weight * Base_Prior) / (N + Prior_Weight)
            shrunk_confidence = (
                effective_successes + self.laplace_prior_weight * self.base_success_prior
            ) / (evidence_count + self.laplace_prior_weight)

            # Determine status
            if evidence_count >= self.min_evidence and shrunk_confidence >= self.min_confidence:
                status = "ACTIVE"
            elif evidence_count >= self.min_evidence:
                status = "PROBATION"
            else:
                status = "SPARSE"

            # Last observed timestamp
            timestamps = sorted([ts for ts in data['timestamps'] if ts])
            last_observed = timestamps[-1] if timestamps else "Unknown"

            pid = f"PW_{intent[:4]}_{pathway_counter:04d}"
            pathway_counter += 1

            pathway = SupportPathway(
                pathway_id=pid,
                intent=intent,
                conditions=data['conditions_dict'],
                action=action_name,
                outcome_distribution=outcomes,
                evidence_count=evidence_count,
                recent_evidence_count=int(evidence_count * 0.3), # Recent window fraction
                pathway_confidence=round(float(shrunk_confidence), 4),
                last_observed=last_observed,
                supporting_conversations=list(data['conversations'])[:20],
                sample_customer_queries=data.get('customer_queries', []),
                sample_agent_responses=data['agent_responses'],
                status=status
            )
            pathways.append(pathway)

        # Sort by evidence count descending
        pathways.sort(key=lambda p: (p.status == 'ACTIVE', p.evidence_count), reverse=True)
        return pathways
