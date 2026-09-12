import re
from typing import List, Dict, Any, Tuple

class OutcomeInferenceEngine:
    """
    Infers conversation thread outcomes across exactly four explicit categories:
      1. RESOLVED: Reasonably strong evidence of customer issue resolution.
      2. LIKELY_RESOLVED: Plausible resolution/guidance followed by courteous customer closing without complaints.
      3. ESCALATED: Conversation transitioned to private DM, phone line, or backstage engineering investigation.
      4. UNRESOLVED_OPEN: Conversation trailed off or ended without resolution or escalation signals.
    """
    OUTCOME_DESCRIPTIONS = {
        'RESOLVED': 'Explicit customer confirmation of successful issue resolution.',
        'LIKELY_RESOLVED': 'Agent provided complete resolution steps and customer acknowledged without further complaint.',
        'ESCALATED': 'Conversation redirected to private DM or backstage specialist handling.',
        'UNRESOLVED_OPEN': 'Thread ended without confirmed resolution or explicit escalation.'
    }

    @classmethod
    def infer_outcome(cls, turns: List[Dict[str, Any]]) -> Tuple[str, str, float]:
        """
        Infers outcome from complete conversation turns.
        Returns (outcome_label, evidence_summary, confidence_score).
        """
        cust_turns = [t for t in turns if t.get('inbound') or t.get('author_type') == 'customer']
        agent_turns = [t for t in turns if not t.get('inbound') and (t.get('author_id') == 'SpotifyCares' or t.get('author_type') == 'support')]

        if not agent_turns:
            return 'UNRESOLVED_OPEN', 'No agent responses recorded in thread.', 0.90

        last_cust_text = cust_turns[-1]['text'].lower() if cust_turns else ""
        last_agent_text = agent_turns[-1]['text'].lower() if agent_turns else ""

        # 1. Check for explicit RESOLVED confirmation by customer
        res_match = re.search(r'\b(fixed it|works now|working now|it worked|that worked|sorted now|resolved|all good now|thanks that helped|brilliant thanks|worked thanks|got it working|fixed thanks|solved)\b', last_cust_text)
        if res_match:
            return 'RESOLVED', f'Customer confirmed: "{res_match.group(0)}"', 0.95

        # 2. Check if agent confirmed customer fix
        agent_res_match = re.search(r'\b(glad to hear|great to hear.*fixed|happy to help.*working|glad.*sorted|glad to hear that)\b', last_agent_text)
        if agent_res_match:
            return 'RESOLVED', f'Agent acknowledged: "{agent_res_match.group(0)}"', 0.90

        # 3. Check for LIKELY_RESOLVED (customer thanks after substantive guidance without further complaint)
        thanks_match = re.search(r'\b(thank you|thanks|thx|cheers|awesome thanks|appreciate it|ok thanks|will do|got it thanks|understood)\b', last_cust_text)
        unresolved_complaint = bool(re.search(r'\b(not working|still|didn\'t work|doesn\'t work|error|fail|why|useless|broken)\b', last_cust_text))
        if thanks_match and not unresolved_complaint and len(turns) >= 3:
            return 'LIKELY_RESOLVED', f'Customer acknowledged guidance: "{thanks_match.group(0)}"', 0.80

        # 4. Check for ESCALATED (Agent redirected to DM / private channel or internal team)
        dm_match = re.search(r'\b(dm|direct message|private message|backstage|specialist|pass.*team|engineering)\b', last_agent_text)
        if dm_match:
            return 'ESCALATED', f'Agent redirected: "{dm_match.group(0)}"', 0.92

        # 5. Fallback: UNRESOLVED_OPEN
        return 'UNRESOLVED_OPEN', 'Thread ended without verified resolution or escalation.', 0.85
