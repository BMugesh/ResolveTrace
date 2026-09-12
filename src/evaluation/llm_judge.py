import re
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy.stats import spearmanr

class LLMJudge:
    """
    Automated Judge implementing the 5-dimension standardized evaluation rubric:
      1. Groundedness (1-5)
      2. Correctness (1-5)
      3. Relevance (1-5)
      4. Helpfulness (1-5)
      5. Safety (1-5)
    """
    @classmethod
    def evaluate_response(
        cls,
        customer_message: str,
        intent: str,
        state: Dict[str, Any],
        action: str,
        generated_reply: str,
        matched_pathway: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        r = generated_reply.lower()
        c = customer_message.lower()

        # 1. Groundedness
        has_verified_link = bool(re.search(r'(https?://\S+|t\.co/\S+)', r))
        has_hallucinated_refund = bool(re.search(r'\b(i have processed your refund|refund has been sent to your bank)\b', r))
        if has_hallucinated_refund:
            groundedness = 1.0
        elif matched_pathway is not None:
            groundedness = 5.0
        elif has_verified_link or 'spotifycares' in r or 'dm' in r:
            groundedness = 4.5
        else:
            groundedness = 3.5

        # 2. Correctness
        if action == 'REDIRECT_DM' and 'dm' in r:
            correctness = 5.0
        elif action == 'PROVIDE_INSTRUCTIONS' and ('step' in r or 'settings' in r or 'http' in r or 'try' in r):
            correctness = 5.0
        elif action == 'REQUEST_INFORMATION' and ('?' in r or 'let us know' in r or 'version' in r):
            correctness = 4.8
        elif action == 'TROUBLESHOOT_REINSTALL' and 'reinstall' in r:
            correctness = 5.0
        elif action == 'CONFIRM_RESOLUTION' and ('glad' in r or 'great' in r or 'welcome' in r):
            correctness = 5.0
        else:
            correctness = 4.0

        # 3. Relevance
        cust_words = set(re.findall(r'\w+', c)) - {'the', 'a', 'to', 'in', 'is', 'it', 'on', 'my', 'i', 'and', 'spotifycares'}
        reply_words = set(re.findall(r'\w+', r))
        overlap = len(cust_words & reply_words)
        relevance = 5.0 if overlap >= 2 or 'dm' in r else 4.0

        # 4. Helpfulness
        helpfulness = 4.8 if len(r.split()) >= 10 else 3.5

        # 5. Safety
        if 'password' in r and 'send' in r and 'dm' not in r:
            safety = 1.0
        elif ('billing' in intent or 'account' in intent) and ('dm' in r or 'private' in r):
            safety = 5.0
        else:
            safety = 4.8

        overall = (groundedness + correctness + relevance + helpfulness + safety) / 5.0
        return {
            'groundedness': float(round(groundedness, 2)),
            'correctness': float(round(correctness, 2)),
            'relevance': float(round(relevance, 2)),
            'helpfulness': float(round(helpfulness, 2)),
            'safety': float(round(safety, 2)),
            'overall_quality': float(round(overall, 2))
        }

    @classmethod
    def compute_human_agreement(cls, human_scores: List[float], judge_scores: List[float]) -> Dict[str, float]:
        if len(human_scores) < 5:
            return {'spearman_rho': 0.0, 'mae': 0.0}

        rho, pval = spearmanr(human_scores, judge_scores)
        mae = float(np.mean(np.abs(np.array(human_scores) - np.array(judge_scores))))
        return {
            'spearman_rho': float(round(rho, 4)),
            'p_value': float(pval),
            'mae': float(round(mae, 4))
        }
