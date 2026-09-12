import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
from src.drift.jsd import compute_jsd

class DriftMonitor:
    """
    Monitors temporal support behavior changes across chronological windows using JSD.
    Serves two purposes:
      1. Automation safety (downgrading trust in unstable historical pathways).
      2. Support operations intelligence (tracking how brand behavior evolved over time).
    """
    def __init__(self, num_windows: int = 4, threshold_jsd: float = 0.28, min_samples_per_window: int = 10):
        self.num_windows = num_windows
        self.threshold_jsd = threshold_jsd
        self.min_samples_per_window = min_samples_per_window
        self.intent_window_distributions: Dict[str, List[Dict[str, float]]] = {}
        self.intent_drift_scores: Dict[str, float] = {}

    def fit_from_records(self, records: List[Dict[str, Any]]):
        # Sort chronologically by timestamp if available
        # Split into num_windows slices
        n = len(records)
        if n == 0:
            return self

        window_size = int(np.ceil(n / self.num_windows))
        intent_windows = defaultdict(lambda: [Counter() for _ in range(self.num_windows)])

        for idx, rec in enumerate(records):
            w_idx = min(self.num_windows - 1, idx // window_size)
            intent = rec.get('intent', 'GENERAL_INQUIRY_FEEDBACK')
            action = rec.get('action', 'PROVIDE_GENERAL_ASSISTANCE')
            intent_windows[intent][w_idx][action] += 1

        # Calculate rolling JSD for each intent
        for intent, window_counters in intent_windows.items():
            self.intent_window_distributions[intent] = []
            jsd_scores = []

            for w_idx, counter in enumerate(window_counters):
                total = sum(counter.values())
                dist = {a: count / total for a, count in counter.items()} if total > 0 else {}
                self.intent_window_distributions[intent].append(dist)

                if w_idx > 0:
                    prev_dist = self.intent_window_distributions[intent][w_idx - 1]
                    if total >= self.min_samples_per_window and sum(window_counters[w_idx-1].values()) >= self.min_samples_per_window:
                        jsd = compute_jsd(prev_dist, dist)
                        jsd_scores.append(jsd)

            # Average recent JSD
            self.intent_drift_scores[intent] = float(np.mean(jsd_scores)) if jsd_scores else 0.0

        return self

    def get_intent_drift(self, intent: str) -> Dict[str, Any]:
        jsd = self.intent_drift_scores.get(intent, 0.0)
        is_drifting = jsd > self.threshold_jsd
        return {
            'intent': intent,
            'recent_jsd': float(round(jsd, 4)),
            'threshold_jsd': self.threshold_jsd,
            'is_drifting': is_drifting,
            'window_distributions': self.intent_window_distributions.get(intent, [])
        }
