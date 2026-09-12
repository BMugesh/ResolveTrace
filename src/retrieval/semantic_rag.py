import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SemanticRAGBaseline:
    """
    Baseline C: Semantic RAG.
    Retrieves the most semantically similar historical customer tweet and copies/adapts the historical agent reply.
    Does NOT use explicit state schemas or decision pathways.
    """
    def __init__(self, max_features: int = 10000):
        self.vectorizer = TfidfVectorizer(max_features=max_features, stop_words='english')
        self.corpus_messages: List[str] = []
        self.corpus_replies: List[str] = []
        self.corpus_actions: List[str] = []
        self.corpus_intents: List[str] = []
        self.tfidf_matrix = None

    def fit(self, training_records: List[Dict[str, Any]]):
        self.corpus_messages = [r['customer_text'] for r in training_records]
        self.corpus_replies = [r['agent_text'] for r in training_records]
        self.corpus_actions = [r.get('action', 'PROVIDE_GENERAL_ASSISTANCE') for r in training_records]
        self.corpus_intents = [r.get('intent', 'GENERAL_INQUIRY_FEEDBACK') for r in training_records]
        
        self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_messages)
        return self

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]
        top_indices = np.argsort(sims)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append({
                'similarity_score': float(sims[idx]),
                'customer_text': self.corpus_messages[idx],
                'agent_reply': self.corpus_replies[idx],
                'historical_action': self.corpus_actions[idx],
                'historical_intent': self.corpus_intents[idx]
            })
        return results
