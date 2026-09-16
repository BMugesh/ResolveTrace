import re
from typing import Dict, Any, Tuple, Optional

class AgentActionExtractor:
    """
    Extracts controlled vocabulary agent actions from SpotifyCares support response text.
    """
    ACTIONS_METADATA = {
        'REQUEST_INFO_AND_REDIRECT_DM': {
            'description': 'Agent asks diagnostic clarifying questions and invites customer to private Direct Message.',
            'category': 'Diagnostics & Private Routing'
        },
        'REQUEST_INFORMATION': {
            'description': 'Agent asks diagnostic questions regarding device model, OS/app versions, or symptom behavior.',
            'category': 'Diagnostics'
        },
        'PROVIDE_INSTRUCTIONS': {
            'description': 'Agent provides concrete step-by-step instructions, settings navigation, or official support links.',
            'category': 'Resolution Guidance'
        },
        'REDIRECT_DM': {
            'description': 'Agent directly requests customer to send a private DM for account investigation or security.',
            'category': 'Private Routing'
        },
        'PROVIDE_GENERAL_ASSISTANCE': {
            'description': 'Agent offers general troubleshooting, acknowledges inquiry, or provides open assistance.',
            'category': 'General Support'
        },
        'ESCALATE_INTERNAL': {
            'description': 'Agent escalates case to backstage specialists, developer team, or specialized billing support.',
            'category': 'Escalation'
        },
        'CONFIRM_RESOLUTION': {
            'description': 'Agent confirms with customer that problem is solved or celebrates positive resolution.',
            'category': 'Resolution Confirmation'
        },
        'CLOSING_COURTESY': {
            'description': 'Agent sends courteous sign-off pleasantries ("You are welcome", "Have a great day").',
            'category': 'Courtesy'
        },
        'TROUBLESHOOT_REINSTALL': {
            'description': 'Agent instructs customer to perform a clean reinstall or clear local app cache/data.',
            'category': 'Technical Troubleshooting'
        },
        'TROUBLESHOOT_UPDATE': {
            'description': 'Agent instructs customer to update the Spotify app or OS to the latest release.',
            'category': 'Technical Troubleshooting'
        },
        'TROUBLESHOOT_RESTART': {
            'description': 'Agent instructs customer to reboot device or power cycle hardware.',
            'category': 'Technical Troubleshooting'
        },
        'EXPLAIN_POLICY_OR_CATALOG': {
            'description': 'Agent explains licensing agreements, artist rights, content availability, or feature terms.',
            'category': 'Policy & Catalog'
        }
    }

    @classmethod
    def extract_action(cls, agent_text: str) -> Dict[str, Any]:
        t = agent_text.lower()
        t_no_url = re.sub(r'https?://\S+', '', t)
        
        # Word boundary DM check on non-URL text to prevent t.co hash substring collisions
        has_dm = bool(re.search(r'\b(dm|direct message|private message|pm|join us in a dm)\b', t_no_url)) or 'ldfdzrinat' in t or 'twitter.com/messages' in t
        
        # Strip closing courtesy phrases to prevent 'anything else' / 'give us a shout' false positives
        t_no_courtesy = re.sub(r'\b(if (there\'s|you need) anything else|let us know if there\'s anything else|anything else (we can|that we can)|just give us a shout)\b.*', '', t_no_url)
        has_question = '?' in t_no_courtesy or bool(re.search(r'\b(which|what|could you let us know|let us know|tell us|send us|(can you|could you|please) share|confirm|are you on|have you tried|can you check|could you confirm)\b', t_no_courtesy))
        
        has_restart = bool(re.search(r'\b(restart|reboot|turn off and on|power cycle|force restart|turn your device off)\b', t))
        has_update = bool(re.search(r'\b(update to|latest version|update the app|update your|app store|play store|latest update)\b', t)) and not bool(re.search(r'\b(since the update|after the update|with the update|was it after|after an app update)\b', t))
        has_reinstall = bool(re.search(r'\b(clean reinstall|reinstall|uninstall and reinstall|delete and reinstall|delete the app|re-install)\b', t))
        has_instruction = bool(re.search(r'\b(settings\s*>|tap|select|go to|click|check out|steps|guide|article|try this|head over to|here\'s how)\b', t)) or ('http' in t and not has_dm)
        has_catalog = bool(re.search(r'\b(music licensing|content availability|rights|licensing agreements|pass that suggestion|catalog|distributor|aggregator)\b', t))
        has_escalate = bool(re.search(r'\b(escalat|backstage|specialist|pass.*team|engineering team|investigat|look into this backstage|look into this with our team)\b', t))
        has_resolution = bool(re.search(r'\b(glad to hear|great to hear|happy that helped|all sorted|glad.*working|glad.*fixed|awesome news)\b', t))
        has_courtesy = bool(re.search(r'\b(you\'re welcome|no problem|anytime|just give us a shout|we\'re here for you|happy to help|have a great day|have a good one)\b', t))

        if has_resolution:
            action_name = 'CONFIRM_RESOLUTION'
            evidence = re.search(r'\b(glad to hear|great to hear|happy that helped|all sorted|glad.*working|glad.*fixed|awesome news)\b', t).group(0)
            confidence = 0.95
        elif has_reinstall:
            action_name = 'TROUBLESHOOT_REINSTALL'
            evidence = re.search(r'\b(clean reinstall|reinstall|uninstall and reinstall|delete and reinstall|delete the app|re-install)\b', t).group(0)
            confidence = 0.92
        elif has_restart:
            action_name = 'TROUBLESHOOT_RESTART'
            evidence = re.search(r'\b(restart|reboot|turn off and on|power cycle|force restart|turn your device off)\b', t).group(0)
            confidence = 0.90
        elif has_update and ('try' in t or 'ensure' in t or 'make sure' in t or 'update' in t):
            action_name = 'TROUBLESHOOT_UPDATE'
            evidence = "Instructed update to latest release"
            confidence = 0.88
        elif has_catalog:
            action_name = 'EXPLAIN_POLICY_OR_CATALOG'
            evidence = re.search(r'\b(music licensing|content availability|rights|licensing agreements|pass that suggestion|catalog|distributor|aggregator)\b', t).group(0)
            confidence = 0.88
        elif has_dm and (has_question or bool(re.search(r'\b(email|username|account|country|screenshot|details|address|statement)\b', t_no_url))):
            action_name = 'REQUEST_INFO_AND_REDIRECT_DM'
            evidence = "Asked diagnostic details and provided DM routing link"
            confidence = 0.93
        elif has_dm:
            action_name = 'REDIRECT_DM'
            evidence = "Requested private DM"
            confidence = 0.92
        elif has_escalate:
            action_name = 'ESCALATE_INTERNAL'
            evidence = re.search(r'\b(escalat|backstage|specialist|pass.*team|engineering team|investigat|look into this backstage|look into this with our team)\b', t).group(0)
            confidence = 0.90
        elif has_instruction:
            action_name = 'PROVIDE_INSTRUCTIONS'
            evidence = "Provided navigational steps or documentation link"
            confidence = 0.88
        elif has_question:
            action_name = 'REQUEST_INFORMATION'
            evidence = "Asked diagnostic questions"
            confidence = 0.85
        elif has_courtesy:
            action_name = 'CLOSING_COURTESY'
            evidence = "Sent courteous closing remarks"
            confidence = 0.85
        else:
            action_name = 'PROVIDE_GENERAL_ASSISTANCE'
            evidence = "General support response"
            confidence = 0.70

        return {
            'action': action_name,
            'description': cls.ACTIONS_METADATA.get(action_name, {}).get('description', ''),
            'evidence_span': evidence,
            'confidence': confidence
        }
