import re
from typing import List, Dict, Any, Optional, Tuple
from src.state.schema import CustomerState

class StateExtractor:
    """
    Extracts the customer situation state and associated text evidence from conversation turns.
    """
    DEVICE_PATTERNS = [
        ('iPhone', r'\b(iphone|ipod|ios)\b'),
        ('iPad', r'\b(ipad)\b'),
        ('Mac', r'\b(macbook|mac|imac|macos|osx|mac mini)\b'),
        ('Apple Watch', r'\b(apple watch|iwatch|watchos)\b'),
        ('Apple TV', r'\b(apple tv|appletv|tvos)\b'),
        ('Android', r'\b(android|samsung|galaxy|pixel|huawei|xiaomi|nexus|oneplus|lg|motorola|xperia|htc)\b'),
        ('Windows/PC', r'\b(windows|win10|win11|win8|win7|pc|laptop|desktop|surface)\b'),
        ('Audio/Accessory', r'\b(speaker|bluetooth|echo|alexa|sonos|carplay|android auto|headphone|earbuds|airpod|airpods|headset|soundbar|stereo)\b'),
        ('Smart TV/Console', r'\b(ps4|ps5|playstation|xbox|roku|smart tv|chromecast|firetv|fire tv)\b'),
        ('Mobile/Phone', r'\b(phone|mobile|smartphone|cellphone|cell|handset|cellular|4g|3g|lte|wi-?fi)\b')
    ]

    @classmethod
    def extract_device(cls, text: str) -> Tuple[str, Optional[str]]:
        t = text.lower()
        for device_name, pattern in cls.DEVICE_PATTERNS:
            match = re.search(pattern, t)
            if match:
                return device_name, match.group(0)
        return "unknown", None

    @classmethod
    def extract_from_turns(
        cls,
        customer_texts: List[str],
        previous_agent_texts: Optional[List[str]] = None,
        turn_index: int = 1
    ) -> CustomerState:
        if previous_agent_texts is None:
            previous_agent_texts = []

        combined_cust = " ".join(customer_texts)
        t_cust = combined_cust.lower()
        combined_agent = " ".join(previous_agent_texts)
        t_agent = combined_agent.lower()

        evidence = {}

        # 1. Device type
        device_type, dev_evidence = cls.extract_device(combined_cust)
        if dev_evidence:
            evidence['device_type'] = dev_evidence

        # 2. OS version
        os_match = re.search(r'\b(ios\s*\d+(\.\d+)*|android\s*\d+(\.\d+)*|macos\s*\d+(\.\d+)*|win\s*\d+|windows\s*\d+|version\s*\d+\.\d+)\b', t_cust)
        os_version_provided = bool(os_match)
        if os_match:
            evidence['os_version'] = os_match.group(0)

        # 3. App version
        app_match = re.search(r'\b(v\d+\.\d+(\.\d+)*|version\s*\d+\.\d+(\.\d+)*|spotify\s*version\s*\d+)\b', t_cust)
        app_version_provided = bool(app_match)
        if app_match:
            evidence['app_version'] = app_match.group(0)

        # 4. Error message / code
        err_match = re.search(r'\b(error code \d+|error:\s*[\w\s]+|says\s*[\'"][^\'"]+[\'"]|shows\s*an\s*error|screenshot|popup|alert)\b', t_cust)
        error_message_provided = bool(err_match)
        if err_match:
            evidence['error_message'] = err_match.group(0)

        # 5. Info provided
        has_detail = len(combined_cust.split()) >= 6
        info_provided = bool(device_type != "unknown" or os_version_provided or app_version_provided or error_message_provided or has_detail)
        if info_provided:
            evidence['info_provided'] = "Diagnostic details or context provided in message"

        # 6. Troubleshoot attempted
        tr_match = re.search(r'\b(tried|already tried|restarted|rebooted|reinstalled|reset|cleared cache|uninstalled|updated|done all)\b', t_cust)
        troubleshoot_attempted = bool(tr_match)
        if tr_match:
            evidence['troubleshoot_attempted'] = tr_match.group(0)

        # 7. Issue recurring
        rec_match = re.search(r'\b(still|again|keeps|repeatedly|every time|always|constantly|everyday|for days|since yesterday|won\'t stop|persists)\b', t_cust)
        issue_recurring = bool(rec_match)
        if rec_match:
            evidence['issue_recurring'] = rec_match.group(0)

        # 8. Billing related
        bill_match = re.search(r'\b(charged|charge|billed|billing|subscription|refund|receipt|invoice|payment|money|cost|price|card|bank)\b', t_cust)
        billing_related = bool(bill_match)
        if bill_match:
            evidence['billing_related'] = bill_match.group(0)

        # 9. Sentiment frustrated
        frust_match = re.search(r'\b(frustrat|angry|annoy|pissed|hate|sucks|terrible|horrible|useless|worst|ridiculous|wtf|fucking|broken|ruined|crap|shit|fix this)\b', t_cust)
        sentiment_frustrated = bool(frust_match) or ('!' in combined_cust and ('why' in t_cust or 'never' in t_cust))
        if sentiment_frustrated:
            evidence['sentiment_frustrated'] = frust_match.group(0) if frust_match else "High emotional frustration markers"

        # 10. Channel DM redirected
        dm_match = re.search(r'\b(dm|direct message|private message|pm)\b', t_agent)
        channel_dm_redirected = bool(dm_match)
        if dm_match:
            evidence['channel_dm_redirected'] = dm_match.group(0)

        # 11. Is ambiguous (sparse query or gibberish)
        words = [w for w in combined_cust.split() if not w.startswith('@')]
        is_ambiguous = len(words) <= 2 or len(combined_cust.strip()) < 15 or bool(re.search(r'^[^\x00-\x7F]+$', combined_cust.strip()))

        return CustomerState(
            info_provided=info_provided,
            troubleshoot_attempted=troubleshoot_attempted,
            issue_recurring=issue_recurring,
            billing_related=billing_related,
            device_type=device_type,
            os_version_provided=os_version_provided,
            app_version_provided=app_version_provided,
            error_message_provided=error_message_provided,
            sentiment_frustrated=sentiment_frustrated,
            channel_dm_redirected=channel_dm_redirected,
            turn_index=turn_index,
            is_ambiguous=is_ambiguous,
            evidence=evidence
        )
