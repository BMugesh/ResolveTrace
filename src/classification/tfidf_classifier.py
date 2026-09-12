import numpy as np
import re
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report

class TfidfIntentClassifier:
    """
    Baseline 2: Simple supervised TF-IDF + Logistic Regression model for intent classification.
    """
    def __init__(self, max_features: int = 5000, ngram_range: Tuple[int, int] = (1, 2), C: float = 1.0):
        self.pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=max_features,
                ngram_range=ngram_range,
                stop_words='english',
                lowercase=True,
                token_pattern=r'(?u)\b\w+\b'
            )),
            ('clf', LogisticRegression(
                C=C,
                max_iter=1000,
                class_weight='balanced',
                random_state=42
            ))
        ])
        self.classes_ = None

    def fit(self, X: List[str], y: List[str]):
        self.pipeline.fit(X, y)
        self.classes_ = self.pipeline.named_steps['clf'].classes_
        return self

    def predict(self, X: List[str]) -> List[str]:
        return self.pipeline.predict(X)

    def predict_proba(self, X: List[str]) -> np.ndarray:
        return self.pipeline.predict_proba(X)

    def predict_with_confidence(self, text: str) -> Tuple[str, float]:
        probs = self.pipeline.predict_proba([text])[0]
        max_idx = np.argmax(probs)
        predicted_class = self.classes_[max_idx]
        confidence = float(probs[max_idx])
        return predicted_class, confidence
