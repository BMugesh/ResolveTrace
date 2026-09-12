from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional

@dataclass
class SupportPathway:
    """
    The fundamental atomic knowledge unit in ResolveTrace:
    Customer Situation (Intent + State) -> Support Decision (Action) -> Outcome Distribution + Evidence + Confidence
    """
    pathway_id: str
    intent: str
    conditions: Dict[str, Any]
    action: str
    outcome_distribution: Dict[str, int]
    evidence_count: int
    recent_evidence_count: int
    pathway_confidence: float
    last_observed: str
    supporting_conversations: List[str] = field(default_factory=list)
    sample_customer_queries: List[str] = field(default_factory=list)
    sample_agent_responses: List[str] = field(default_factory=list)
    status: str = "ACTIVE" # ACTIVE, SPARSE, PROBATION, DEPRECATED

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SupportPathway':
        return cls(**data)
