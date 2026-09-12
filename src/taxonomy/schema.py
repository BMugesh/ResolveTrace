import yaml
from typing import Dict, List, Any

class IntentTaxonomy:
    """
    Manages the frozen SpotifyCares intent taxonomy schema.
    """
    def __init__(self, taxonomy_path: str = "configs/taxonomy.yaml"):
        with open(taxonomy_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        self.intents: Dict[str, Dict[str, Any]] = data['intents']
        self.intent_names: List[str] = list(self.intents.keys())

    def get_intent_info(self, intent_name: str) -> Dict[str, Any]:
        return self.intents.get(intent_name, {
            "name": intent_name,
            "description": "Unknown or unclassified intent",
            "examples": []
        })

    def validate_intent(self, intent_name: str) -> bool:
        return intent_name in self.intents
