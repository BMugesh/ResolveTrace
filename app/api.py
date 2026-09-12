from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import sys
import yaml
import pandas as pd

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classification.tfidf_classifier import TfidfIntentClassifier
from src.state.extractor import StateExtractor
from src.playbook.store import PlaybookStore
from src.playbook.matcher import PathwayMatcher
from src.decision.engine import DecisionEngine
from src.generation.grounded_generator import GroundedResponseGenerator
from src.drift.monitor import DriftMonitor

app = FastAPI(
    title="ResolveTrace API — Historical Support Playbook",
    description="REST API for SpotifyCares support decision pathway matching, safety gating, and grounded reply generation.",
    version="1.0.0"
)

# Global instances
with open('configs/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

df_turns = pd.read_csv(config['paths']['spotify_turn_csv'])
train_recs = df_turns.head(15000).to_dict('records')

tfidf_clf = TfidfIntentClassifier().fit(
    [r['customer_text'] for r in train_recs],
    [r['intent'] for r in train_recs]
)
store = PlaybookStore(config['paths']['playbook_json'])
matcher = PathwayMatcher(store.pathways, training_records=train_recs)
engine = DecisionEngine(matcher, thresholds_path="configs/thresholds.yaml")
drift_monitor = DriftMonitor().fit_from_records(train_recs)

class EvaluateCaseRequest(BaseModel):
    customer_message: str

class EvaluateCaseResponse(BaseModel):
    intent: str
    intent_confidence: float
    state: Dict[str, Any]
    decision: str
    recommended_action: str
    reason: str
    automation_score: float
    matched_pathway_id: Optional[str]
    draft_reply: str

@app.get("/health")
def health():
    return {"status": "healthy", "brand": "SpotifyCares", "active_pathways": len(store.get_active_pathways())}

@app.post("/evaluate", response_model=EvaluateCaseResponse)
def evaluate_case(request: EvaluateCaseRequest):
    msg = request.customer_message
    if not msg.strip():
        raise HTTPException(status_code=400, detail="Customer message cannot be empty.")

    intent, intent_conf = tfidf_clf.predict_with_confidence(msg)
    state = StateExtractor.extract_from_turns([msg])
    eval_res = engine.evaluate_case(
        customer_text=msg,
        intent=intent,
        intent_confidence=intent_conf,
        state=state,
        drift_monitor=drift_monitor
    )
    matched_p = eval_res['matched_pathway']
    draft_reply = GroundedResponseGenerator.generate(
        intent=intent,
        state=state,
        action=eval_res['recommended_action'],
        matched_pathway=matched_p
    )

    return EvaluateCaseResponse(
        intent=intent,
        intent_confidence=float(round(intent_conf, 4)),
        state=state.to_dict(),
        decision=eval_res['decision'],
        recommended_action=eval_res['recommended_action'],
        reason=eval_res['reason'],
        automation_score=float(round(eval_res['automation_score'], 4)),
        matched_pathway_id=matched_p['pathway_id'] if matched_p else None,
        draft_reply=draft_reply
    )

@app.get("/playbook/pathways")
def list_pathways(intent: Optional[str] = None, status: Optional[str] = None):
    pws = store.pathways
    if intent:
        pws = [p for p in pws if p.intent == intent]
    if status:
        pws = [p for p in pws if p.status == status]
    return {"total": len(pws), "pathways": [p.to_dict() for p in pws[:50]]}
