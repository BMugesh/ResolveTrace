import numpy as np
import re
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.playbook.schema import SupportPathway
from src.state.schema import CustomerState

class PathwayMatcher:
    """
    Hybrid Situational & Semantic Pathway Matcher.
    Combines:
      1. Intent Filtering & Consistency
      2. State Condition Compatibility (weighted overlap)
      3. Semantic Retrieval against historical pathway query signatures
      4. Turn-context filtering (prevents terminal/closing actions on opening turns)
      5. Bayesian Pathway Confidence & Evidence Scale
    """
    def __init__(
        self,
        pathways: List[SupportPathway],
        training_records: Optional[List[Dict[str, Any]]] = None
    ):
        self.pathways = pathways
        self.training_records = training_records
        
        # Build index from training records if provided, or from pathway signatures
        self.pathway_map = {}
        for p in self.pathways:
            cond_tuple = (
                p.conditions.get('info_provided', False),
                p.conditions.get('troubleshoot_attempted', False),
                p.conditions.get('issue_recurring', False),
                p.conditions.get('billing_related', False),
                p.conditions.get('device_type', 'unknown')
            )
            self.pathway_map[(p.intent, cond_tuple, p.action)] = p

        if self.training_records:
            self.corpus_texts = [r['customer_text'] for r in self.training_records]
            self.vectorizer = TfidfVectorizer(max_features=10000, stop_words='english')
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)
        else:
            self.corpus_texts = []
            for p in self.pathways:
                cust_queries = " ".join(getattr(p, 'sample_customer_queries', []))
                agent_resps = " ".join(p.sample_agent_responses)
                text_sig = f"{p.intent} {p.action} {cust_queries} {agent_resps}"
                self.corpus_texts.append(text_sig)
            self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            if self.corpus_texts:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_texts)
            else:
                self.tfidf_matrix = None

    def match(
        self,
        intent: str,
        state: CustomerState,
        customer_text: str = "",
        top_k: int = 5
    ) -> List[Tuple[SupportPathway, float]]:
        cond_tuple = state.get_condition_tuple()
        c_lower = customer_text.lower()
        has_resolution_keywords = any(w in c_lower for w in ['thanks', 'fixed', 'works now', 'thank you', 'solved'])

        # If training records index is present, perform hybrid evidence voting
        if self.training_records and customer_text and self.tfidf_matrix is not None:
            vec = self.vectorizer.transform([customer_text])
            sims = cosine_similarity(vec, self.tfidf_matrix)[0]
            top_k_indices = np.argsort(sims)[::-1][:25]

            action_scores = defaultdict(float)
            action_best_pws = {}

            for k_idx in top_k_indices:
                rec = self.training_records[k_idx]
                sim = float(sims[k_idx])
                if sim < 0.03:
                    continue

                rec_action = rec['action']
                rec_intent = rec['intent']

                # Action plausibility for opening turn
                if rec_action in ('CONFIRM_RESOLUTION', 'CLOSING_COURTESY') and not has_resolution_keywords:
                    continue

                # State match multiplier
                state_mult = 1.0
                if rec.get('billing_related') == state.billing_related:
                    state_mult += 0.35
                if rec.get('troubleshoot_attempted') == state.troubleshoot_attempted:
                    state_mult += 0.25
                if rec.get('issue_recurring') == state.issue_recurring:
                    state_mult += 0.20

                # Intent consistency multiplier
                intent_mult = 1.6 if rec_intent == intent else 0.5
                score = sim * state_mult * intent_mult
                action_scores[rec_action] += score

                # Associate with the best matching SupportPathway
                if rec_action not in action_best_pws:
                    pw_exact = self.pathway_map.get((intent, cond_tuple, rec_action))
                    if not pw_exact:
                        # Fallback: any pathway with this intent & action
                        matches = [p for p in self.pathways if p.intent == intent and p.action == rec_action]
                        pw_exact = matches[0] if matches else None
                    action_best_pws[rec_action] = pw_exact

            ranked_actions = sorted(action_scores.items(), key=lambda x: x[1], reverse=True)
            results = []
            for act, act_score in ranked_actions:
                pw = action_best_pws.get(act)
                if pw:
                    norm_score = float(round(min(1.0, act_score / (ranked_actions[0][1] + 1e-6)), 4))
                    results.append((pw, norm_score))
            if results:
                return results[:top_k]

        # Standard Pathway Matching Fallback
        sims = np.zeros(len(self.pathways))
        if customer_text and self.tfidf_matrix is not None:
            query_vec = self.vectorizer.transform([customer_text])
            sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        candidate_scores = []
        for idx, p in enumerate(self.pathways):
            if p.status in ('ACTIVE', 'PROBATION'):
                # Intent filtering
                if p.intent != intent:
                    continue

                # Opening turn check
                if p.action in ('CONFIRM_RESOLUTION', 'CLOSING_COURTESY') and not has_resolution_keywords:
                    continue

                cond = p.conditions
                matches = 0
                if cond.get('info_provided') == state.info_provided:
                    matches += 1
                if cond.get('troubleshoot_attempted') == state.troubleshoot_attempted:
                    matches += 1
                if cond.get('issue_recurring') == state.issue_recurring:
                    matches += 1
                if cond.get('billing_related') == state.billing_related:
                    matches += 1
                p_dev = cond.get('device_type', 'unknown')
                s_dev = state.device_type
                if p_dev == s_dev or p_dev == 'unknown' or s_dev == 'unknown':
                    matches += 1
                condition_score = matches / 5.0

                semantic_sim = float(sims[idx]) if idx < len(sims) else 0.0
                confidence_factor = p.pathway_confidence
                evidence_scale = min(1.0, np.log1p(p.evidence_count) / np.log1p(30))

                total_score = (
                    0.35 * condition_score +
                    0.35 * semantic_sim +
                    0.15 * confidence_factor +
                    0.15 * evidence_scale
                )
                if total_score > 0.0:
                    candidate_scores.append((p, float(round(total_score, 4))))

        candidate_scores.sort(key=lambda x: (x[1], x[0].evidence_count), reverse=True)
        return candidate_scores[:top_k]
