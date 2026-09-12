from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, Tuple

@dataclass
class CustomerState:
    """
    Core state schema representing the customer situation at a specific turn.
    Version: 1.0.0
    """
    # Mandatory core state variables
    info_provided: bool = False
    troubleshoot_attempted: bool = False
    issue_recurring: bool = False
    billing_related: bool = False
    device_type: str = "unknown"

    # Data-justified state extensions
    os_version_provided: bool = False
    app_version_provided: bool = False
    error_message_provided: bool = False
    sentiment_frustrated: bool = False
    channel_dm_redirected: bool = False
    turn_index: int = 1
    is_ambiguous: bool = False

    # Evidence traces
    evidence: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_condition_tuple(self) -> Tuple[bool, bool, bool, bool, str]:
        """Compact tuple representation for exact pathway matching."""
        return (
            self.info_provided,
            self.troubleshoot_attempted,
            self.issue_recurring,
            self.billing_related,
            self.device_type
        )
