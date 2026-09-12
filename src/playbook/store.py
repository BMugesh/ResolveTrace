import json
import os
from typing import List, Dict, Any, Optional
from src.playbook.schema import SupportPathway

class PlaybookStore:
    """
    Persistent storage and retrieval index for SupportPlaybook pathways.
    """
    def __init__(self, playbook_path: str = "artifacts/playbook.json"):
        self.playbook_path = playbook_path
        self.pathways: List[SupportPathway] = []
        if os.path.exists(playbook_path):
            self.load()

    def save(self, pathways: List[SupportPathway]):
        self.pathways = pathways
        os.makedirs(os.path.dirname(self.playbook_path), exist_ok=True)
        with open(self.playbook_path, 'w', encoding='utf-8') as f:
            json.dump([p.to_dict() for p in pathways], f, indent=2)

    def load(self):
        with open(self.playbook_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.pathways = [SupportPathway.from_dict(d) for d in data]

    def get_active_pathways(self) -> List[SupportPathway]:
        return [p for p in self.pathways if p.status == "ACTIVE"]

    def get_by_intent(self, intent: str) -> List[SupportPathway]:
        return [p for p in self.pathways if p.intent == intent]

    def get_by_id(self, pathway_id: str) -> Optional[SupportPathway]:
        for p in self.pathways:
            if p.pathway_id == pathway_id:
                return p
        return None
