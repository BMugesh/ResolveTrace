from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
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

# CORS Configuration
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
if cors_origins_env:
    origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    matched_pathway_id: Optional[str] = None
    matched_pathway: Optional[Dict[str, Any]] = None
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
    if matched_p:
        # Construct real historical examples from sample queries and agent responses
        examples = []
        queries = matched_p.get('sample_customer_queries') or []
        responses = matched_p.get('sample_agent_responses') or []
        threads = matched_p.get('supporting_conversations') or []
        for i in range(min(len(queries), len(responses))):
            tid = str(threads[i]) if i < len(threads) else str(i + 1)
            examples.append({
                "thread_id": f"TH_{tid}",
                "customer_message": queries[i],
                "agent_reply": responses[i],
                "outcome": matched_p.get('action') or "RESOLVED"
            })
        matched_p['historical_examples'] = examples

    draft_reply = GroundedResponseGenerator.generate(
        intent=intent,
        state=state,
        action=eval_res['recommended_action'],
        matched_pathway=matched_p,
        customer_text=msg,
        decision=eval_res['decision']
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
        matched_pathway=matched_p,
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

@app.get("/metrics")
def get_evaluation_metrics():
    metrics_path = "artifacts/metrics.json"
    pathway_metrics_path = "artifacts/pathway_metrics.json"
    
    metrics_data = {}
    if os.path.exists(metrics_path):
        with open(metrics_path, "r", encoding="utf-8") as f:
            metrics_data = json.load(f)
            
    pathway_metrics_data = {}
    if os.path.exists(pathway_metrics_path):
        with open(pathway_metrics_path, "r", encoding="utf-8") as f:
            pathway_metrics_data = json.load(f)
            
    return {
        "metrics": metrics_data,
        "pathway_metrics": pathway_metrics_data
    }
