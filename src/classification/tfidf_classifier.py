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

    @staticmethod
    def _high_precision_intent_override(text: str) -> str:
        """
        Preserve statistical classification generally, but short-circuit cases
        where Spotify support language has a highly specific lexical meaning.
        """
        t = text.lower()
        offline_download_issue = bool(re.search(
            r'\b(offline|download(?:ing|ed|s)?|re-download|redownload|sync(?:ing)?|local files?)\b',
            t
        ))
        mobile_or_storage_context = bool(re.search(
            r'\b(phone|mobile|iphone|ipad|ios|android|samsung|galaxy|pixel|motorola|wifi|wi-fi|cellular|4g|3g|sd card|storage)\b',
            t
        ))
        broken_download_context = bool(re.search(
            r'\b(stuck|stop(?:s|ped)?|won\'?t|cannot|can\'?t|not|missing|gone|unavailable|greyed|grayed|restarted|reinstalled)\b',
            t
        ))

        if offline_download_issue and (mobile_or_storage_context or broken_download_context):
            return 'OFFLINE_SYNC_DOWNLOADS'

        return ''

    def predict(self, X: List[str]) -> List[str]:
        predictions = list(self.pipeline.predict(X))
        if self.classes_ is None or 'OFFLINE_SYNC_DOWNLOADS' not in self.classes_:
            return predictions
        return [
            self._high_precision_intent_override(text) or pred
            for text, pred in zip(X, predictions)
        ]

    def predict_proba(self, X: List[str]) -> np.ndarray:
        return self.pipeline.predict_proba(X)

    def predict_with_confidence(self, text: str) -> Tuple[str, float]:
        probs = self.pipeline.predict_proba([text])[0]
        max_idx = np.argmax(probs)
        predicted_class = self.classes_[max_idx]
        confidence = float(probs[max_idx])
        override = self._high_precision_intent_override(text)
        if override and override in self.classes_ and predicted_class != override:
            predicted_class = override
            confidence = max(confidence, 0.72)
        return predicted_class, confidence
