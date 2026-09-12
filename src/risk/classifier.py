import re
from typing import Dict, Any, Tuple
from src.state.schema import CustomerState

class RiskClassifier:
    """
    Classifies the operational and business risk of a support case into LOW, MEDIUM, or HIGH.
    """
    RISK_PENALTIES = {
        'LOW': 0.0,
        'MEDIUM': 0.4,
        'HIGH': 0.9
    }

    @classmethod
    def classify_risk(cls, intent: str, state: CustomerState, customer_text: str) -> Dict[str, Any]:
        t = customer_text.lower()
        
        # 1. HIGH Risk Triggers
        # Financial disputes, unauthorized charges, compromised accounts, legal/threats
        high_risk_patterns = [
            r'\b(hacked|compromised|unauthorized|stolen|fraud|bank dispute|lawsuit|attorney|scam)\b',
            r'\b(double charged|overcharged|stole my money|charged multiple times|refund immediately)\b',
            r'\b(someone changed my email|someone logged into my account)\b'
        ]
        
        for p in high_risk_patterns:
            if re.search(p, t):
                return {
                    'risk_level': 'HIGH',
                    'penalty': cls.RISK_PENALTIES['HIGH'],
                    'reason': 'Detected high financial dispute or account security trigger.'
                }

        if intent == 'ACCOUNT_ACCESS_AUTH' and re.search(r'\b(locked out|cannot access|hacked|credentials)\b', t):
            return {
                'risk_level': 'HIGH',
                'penalty': cls.RISK_PENALTIES['HIGH'],
                'reason': 'Account security access restoration required.'
            }

        # 2. MEDIUM Risk Triggers
        # General billing questions, subscription plan changes, family plan address verification
        if intent in ('SUBSCRIPTION_BILLING_PREMIUM', 'FAMILY_PLAN_SETUP', 'STUDENT_DISCOUNT_HULU') or state.billing_related:
            return {
                'risk_level': 'MEDIUM',
                'penalty': cls.RISK_PENALTIES['MEDIUM'],
                'reason': 'Financial, subscription, or eligibility verification inquiry.'
            }

        if state.sentiment_frustrated and state.issue_recurring:
            return {
                'risk_level': 'MEDIUM',
                'penalty': cls.RISK_PENALTIES['MEDIUM'],
                'reason': 'High customer frustration on recurring technical issue.'
            }

        # 3. LOW Risk
        return {
            'risk_level': 'LOW',
            'penalty': cls.RISK_PENALTIES['LOW'],
            'reason': 'Standard technical troubleshooting, playback, or general catalog inquiry.'
        }
