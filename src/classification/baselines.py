import numpy as np
from collections import Counter
from typing import List, Dict, Any
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix

class MajorityClassClassifier:
    """
    Baseline 1: Trivial majority-class predictor.
    Always predicts the single most common intent observed in training data.
    """
    def __init__(self):
        self.majority_class_ = None

    def fit(self, X: List[str], y: List[str]):
        counts = Counter(y)
        self.majority_class_ = counts.most_common(1)[0][0]
        return self

    def predict(self, X: List[str]) -> List[str]:
        if self.majority_class_ is None:
            raise ValueError("Model has not been fitted yet.")
        return [self.majority_class_] * len(X)

    def predict_proba(self, X: List[str]) -> np.ndarray:
        return np.ones((len(X), 1))
