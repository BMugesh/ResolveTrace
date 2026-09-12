import os
import sys
import json
import yaml
import time
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

def run_demo():
    print("=" * 80)
    print("RESOLVETRACE — INTERACTIVE AGENT DEMONSTRATIONS (SPOTIFYCARES)")
    print("=" * 80)

    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 1. Initialize models & Playbook
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

    # Demo 1: AUTO-HANDLE (Strong pathway, low risk, verified state, low drift)
    demo1_msg = "@SpotifyCares How do I clear offline cache and re-download my playlist on iPhone?"
    
    # Demo 2: ESCALATE (High-risk financial charge dispute or security issue)
    demo2_msg = "@SpotifyCares Someone hacked into my account from Russia and changed my email address and password! I need urgent human help!"

    # Demo 3: UNKNOWN (Unseen domain / exotic hardware inquiry -> Playbook Expansion Candidate)
    demo3_msg = "@SpotifyCares Can I connect my smart refrigerator touch screen to Spotify in Korean?"

    demos = [
        ("DEMO 1: AUTO-HANDLE (Confident Pathway + Safe Autonomous Guidance)", demo1_msg),
        ("DEMO 2: ESCALATE (High Risk + Private DM Security Escalation)", demo2_msg),
        ("DEMO 3: UNKNOWN (Unseen Situation -> Playbook Expansion Queue)", demo3_msg)
    ]

    for title, msg in demos:
        print("\n" + "=" * 80)
        print(f"[{title}]")
        print("=" * 80)
        print(f"Customer Tweet : \"{msg}\"")

        # Extraction
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
        reply = GroundedResponseGenerator.generate(
            intent=intent,
            state=state,
            action=eval_res['recommended_action'],
            customer_text=msg,
            matched_pathway=matched_p,
            decision=eval_res['decision']
        )

        print(f"\n--- 1. Situation Analysis ---")
        print(f"  Detected Intent    : {intent} (Confidence: {intent_conf:.1%})")
        print(f"  Device Type        : {state.device_type}")
        print(f"  Info Provided      : {state.info_provided}")
        print(f"  Troubleshoot Tried : {state.troubleshoot_attempted}")
        print(f"  Billing Related    : {state.billing_related}")
        print(f"  Sentiment Frustr.  : {state.sentiment_frustrated}")

        print(f"\n--- 2. Playbook Matching & Safety Evaluation ---")
        if matched_p:
            print(f"  Matched Pathway ID : {matched_p['pathway_id']} (Status: {matched_p['status']})")
            print(f"  Pathway Conditions : {matched_p['conditions']}")
            print(f"  Historical Evidence: {matched_p['evidence_count']} conversations")
            print(f"  Pathway Confidence : {matched_p['pathway_confidence']:.2f}")
        else:
            print(f"  Matched Pathway    : None (No historical match >= threshold tau)")

        print(f"  Risk Assessment    : {eval_res['risk_info']['risk_level']} (Penalty: {eval_res['risk_info']['penalty']}) — {eval_res['risk_info']['reason']}")
        print(f"  Temporal Drift     : JSD = {eval_res['drift_info']['recent_jsd']:.3f} (Drifting: {eval_res['drift_info']['is_drifting']})")
        print(f"  Composite Auto-Score: {eval_res['automation_score']:.2f}")

        print(f"\n--- 3. Decision & Grounded Action ---")
        print(f"  System Decision    : >> {eval_res['decision']} <<")
        print(f"  Decision Rationale : {eval_res['reason']}")
        print(f"  Recommended Action : {eval_res['recommended_action']}")
        print(f"  Draft Reply        : \"{reply}\"")

        if eval_res['decision'] == 'UNKNOWN':
            print(f"\n  [PLAYBOOK EXPANSION QUEUE ENTRY CREATED]")
            print(f"  Reason: Unmapped query situation flagged for human supervisor review and new pathway creation.")

def process_single_message(msg, tfidf_clf, engine, drift_monitor):
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
    reply = GroundedResponseGenerator.generate(
        intent=intent,
        state=state,
        action=eval_res['recommended_action'],
        customer_text=msg,
        matched_pathway=matched_p,
        decision=eval_res['decision']
    )

    print("\n" + "=" * 80)
    print(f"Customer Tweet : \"{msg}\"")
    print("=" * 80)
    print(f"\n--- 1. Situation Analysis ---")
    print(f"  Detected Intent    : {intent} (Confidence: {intent_conf:.1%})")
    print(f"  Device Type        : {state.device_type}")
    print(f"  Info Provided      : {state.info_provided}")
    print(f"  Troubleshoot Tried : {state.troubleshoot_attempted}")
    print(f"  Billing Related    : {state.billing_related}")
    print(f"  Sentiment Frustr.  : {state.sentiment_frustrated}")

    print(f"\n--- 2. Playbook Matching & Safety Evaluation ---")
    if matched_p:
        print(f"  Matched Pathway ID : {matched_p['pathway_id']} (Status: {matched_p['status']})")
        print(f"  Pathway Conditions : {matched_p['conditions']}")
        print(f"  Historical Evidence: {matched_p['evidence_count']} conversations")
        print(f"  Pathway Confidence : {matched_p['pathway_confidence']:.2f}")
    else:
        print(f"  Matched Pathway    : None (No historical match >= threshold tau)")

    print(f"  Risk Assessment    : {eval_res['risk_info']['risk_level']} (Penalty: {eval_res['risk_info']['penalty']}) — {eval_res['risk_info']['reason']}")
    print(f"  Temporal Drift     : JSD = {eval_res['drift_info']['recent_jsd']:.3f} (Drifting: {eval_res['drift_info']['is_drifting']})")
    print(f"  Composite Auto-Score: {eval_res['automation_score']:.2f}")

    print(f"\n--- 3. Decision & Grounded Action ---")
    print(f"  System Decision    : >> {eval_res['decision']} <<")
    print(f"  Decision Rationale : {eval_res['reason']}")
    print(f"  Recommended Action : {eval_res['recommended_action']}")
    print(f"  Draft Reply        : \"{reply}\"")

    if eval_res['decision'] == 'UNKNOWN':
        print(f"\n  [PLAYBOOK EXPANSION QUEUE ENTRY CREATED]")
        print(f"  Reason: Unmapped query situation flagged for human supervisor review and new pathway creation.")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] not in ('--demo', '-d'):
        # Direct query from command line
        custom_query = " ".join(sys.argv[1:])
        with open('configs/config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        df_turns = pd.read_csv(config['paths']['spotify_turn_csv'])
        train_recs = df_turns.head(15000).to_dict('records')
        tfidf_clf = TfidfIntentClassifier().fit([r['customer_text'] for r in train_recs], [r['intent'] for r in train_recs])
        store = PlaybookStore(config['paths']['playbook_json'])
        matcher = PathwayMatcher(store.pathways, training_records=train_recs)
        engine = DecisionEngine(matcher, thresholds_path="configs/thresholds.yaml")
        drift_monitor = DriftMonitor().fit_from_records(train_recs)
        process_single_message(custom_query, tfidf_clf, engine, drift_monitor)
    else:
        run_demo()
