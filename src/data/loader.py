import os
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple

class ConversationLoader:
    """
    Handles serialization, deserialization, and temporal leakage-safe splitting
    of reconstructed support conversation threads.
    """
    @staticmethod
    def save_jsonl(conversations: List[Dict[str, Any]], filepath: str):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            for conv in conversations:
                f.write(json.dumps(conv) + '\n')

    @staticmethod
    def load_jsonl(filepath: str) -> List[Dict[str, Any]]:
        conversations = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    conversations.append(json.loads(line))
        return conversations

    @staticmethod
    def temporal_split(
        conversations: List[Dict[str, Any]],
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Sorts entire conversation threads by opening timestamp and splits them chronologically.
        Ensures NO turns from the same conversation leak across splits.
        """
        # Parse opening timestamp for stable temporal ordering
        for conv in conversations:
            try:
                dt = pd.to_datetime(conv['opening_timestamp'], format='%a %b %d %H:%M:%S +0000 %Y')
            except Exception:
                dt = pd.to_datetime(conv['opening_timestamp'], errors='coerce')
            conv['_parsed_dt'] = dt

        sorted_convs = sorted(conversations, key=lambda x: x['_parsed_dt'])

        # Clean up temporary field
        for conv in sorted_convs:
            del conv['_parsed_dt']

        n = len(sorted_convs)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_set = sorted_convs[:train_end]
        val_set = sorted_convs[train_end:val_end]
        test_set = sorted_convs[val_end:]

        return train_set, val_set, test_set
