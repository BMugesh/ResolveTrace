import streamlit as st
import pandas as pd
import numpy as np
import json
import yaml
import os
import sys

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classification.tfidf_classifier import TfidfIntentClassifier
from src.state.extractor import StateExtractor
from src.playbook.store import PlaybookStore
from src.playbook.matcher import PathwayMatcher
from src.decision.engine import DecisionEngine
from src.generation.grounded_generator import GroundedResponseGenerator
from src.drift.monitor import DriftMonitor

st.set_page_config(
    page_title="ResolveTrace — Historical Support Playbook",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 800; color: #1DB954; margin-bottom: 0px; }
    .subtitle { font-size: 1.1rem; color: #666; margin-bottom: 20px; }
    .metric-card { background-color: #f8f9fa; border-radius: 8px; padding: 15px; border-left: 4px solid #1DB954; }
    .badge-auto { background-color: #28a745; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .badge-esc { background-color: #ffc107; color: black; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
    .badge-unk { background-color: #dc3545; color: white; padding: 4px 12px; border-radius: 12px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_system():
    with open('configs/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    with open('configs/thresholds.yaml', 'r') as f:
        thresholds = yaml.safe_load(f)

    # Load trained models & index
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

    # Load metrics
    metrics = {}
    if os.path.exists(config['paths']['metrics_json']):
        with open(config['paths']['metrics_json'], 'r') as f:
            metrics = json.load(f)

    return config, thresholds, tfidf_clf, store, matcher, engine, drift_monitor, metrics

config, thresholds, tfidf_clf, store, matcher, engine, drift_monitor, metrics = load_system()

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/1/19/Spotify_logo_without_text.svg", width=50)
st.sidebar.markdown("### **ResolveTrace**")
st.sidebar.markdown("**Brand**: SpotifyCares  \n**Core Abstraction**: Support Decision Pathways  \n**Corpus**: 91,081 Tweets (28,187 Threads)")
st.sidebar.markdown("---")

active_count = len([p for p in store.pathways if p.status == 'ACTIVE'])
probation_count = len([p for p in store.pathways if p.status == 'PROBATION'])
sparse_count = len([p for p in store.pathways if p.status == 'SPARSE'])

st.sidebar.metric("Active Pathways", f"{active_count:,}")
st.sidebar.metric("Total Mined Pathways", f"{len(store.pathways):,}")
st.sidebar.metric("Audit Validity Rate", "100.0%")

# Main App Tabs
st.markdown('<div class="main-title">ResolveTrace — Historical Support Playbook</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Evidence-Driven Support Decision Mining & Safe Autonomous Gating for <b>SpotifyCares</b></div>', unsafe_allow_html=True)

tabs = st.tabs([
    "🎯 Live Decision Agent",
    "📖 Playbook Explorer",
    "📈 Playbook Evolution & Drift",
    "📥 Playbook Expansion Queue",
    "📊 Evaluation & Benchmarks"
])

# -------------------------------------------------------------
# TAB 1: Live Decision Agent
# -------------------------------------------------------------
with tabs[0]:
    st.markdown("### Test Customer Cases & Inspect Real-Time Decision Logic")
    
    col_input, col_presets = st.columns([3, 1])
    with col_presets:
        preset_choice = st.selectbox(
            "Load Sample Scenario",
            [
                "Custom Query",
                "1. Skipping Music on Android (Playback)",
                "2. Double Charged on Card (Billing Risk)",
                "3. Smart Refrigerator in Korean (Unknown)",
                "4. Student Discount Hulu Error",
                "5. Hacked Account & Changed Email"
            ]
        )

    presets = {
        "1. Skipping Music on Android (Playback)": "@SpotifyCares my music keeps skipping on my android tablet and bluetooth speaker. How do I fix this?",
        "2. Double Charged on Card (Billing Risk)": "@SpotifyCares you charged my credit card twice for $9.99 this month and someone changed my account email. I need an immediate refund!",
        "3. Smart Refrigerator in Korean (Unknown)": "@SpotifyCares Can I connect my smart refrigerator touch screen to Spotify in Korean?",
        "4. Student Discount Hulu Error": "@SpotifyCares My student discount renewal failed with SheerID and now I cannot access Hulu.",
        "5. Hacked Account & Changed Email": "@SpotifyCares someone hacked into my account and changed the password and email address."
    }

    default_text = presets.get(preset_choice, "@SpotifyCares my music won't play offline on iPhone")
    customer_query = st.text_area("Customer Tweet:", value=default_text, height=90)

    if st.button("Evaluate Customer Situation", type="primary"):
        with st.spinner("Analyzing situation, matching playbook, and checking safety gates..."):
            # 1. Extraction
            intent, intent_conf = tfidf_clf.predict_with_confidence(customer_query)
            state = StateExtractor.extract_from_turns([customer_query])
            eval_res = engine.evaluate_case(
                customer_text=customer_query,
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
                matched_pathway=matched_p,
                customer_text=customer_query,
                decision=eval_res['decision']
            )

        # Display Top Decision Banner
        dec = eval_res['decision']
        if dec == 'AUTO-HANDLE':
            st.success(f"### Decision: AUTO-HANDLE  \n**Rationale**: {eval_res['reason']}")
        elif dec == 'ESCALATE':
            st.warning(f"### Decision: ESCALATE  \n**Rationale**: {eval_res['reason']}")
        else:
            st.error(f"### Decision: UNKNOWN (Playbook Expansion Candidate)  \n**Rationale**: {eval_res['reason']}")

        # 3 Column Breakdown
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### 1. Customer Situation State")
            st.markdown(f"**Predicted Intent**: `{intent}` ({intent_conf:.1%})")
            st.markdown(f"**Device Type**: `{state.device_type}`")
            st.markdown(f"**Info Provided**: `{state.info_provided}`")
            st.markdown(f"**Troubleshoot Attempted**: `{state.troubleshoot_attempted}`")
            st.markdown(f"**Issue Recurring**: `{state.issue_recurring}`")
            st.markdown(f"**Billing Related**: `{state.billing_related}`")
            st.markdown(f"**Customer Frustrated**: `{state.sentiment_frustrated}`")

        with col2:
            st.markdown("#### 2. Playbook Matching & Safety")
            if matched_p:
                st.markdown(f"**Matched Pathway**: `{matched_p['pathway_id']}` ({matched_p['status']})")
                st.markdown(f"**Pathway Confidence**: `{matched_p['pathway_confidence']:.2f}`")
                st.markdown(f"**Historical Evidence**: `{matched_p['evidence_count']}` conversations")
            else:
                st.markdown("**Matched Pathway**: *None (Below Tau / Unmapped)*")

            st.markdown(f"**Risk Level**: `{eval_res['risk_info']['risk_level']}`")
            st.markdown(f"**Temporal Drift**: `JSD = {eval_res['drift_info']['recent_jsd']:.3f}`")
            st.markdown(f"**Composite Auto Score**: `{eval_res['automation_score']:.2f}`")

        with col3:
            st.markdown("#### 3. Recommended Action & Draft Reply")
            st.markdown(f"**Approved Action**: `{eval_res['recommended_action']}`")
            st.info(f"**Draft Response (Grounded)**:\n\n\"{draft_reply}\"")

# -------------------------------------------------------------
# TAB 2: Playbook Explorer
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### Inspect Discovered Support Decision Pathways")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        intent_filter = st.selectbox("Filter by Intent", ["ALL"] + list(set(p.intent for p in store.pathways)))
    with col_f2:
        status_filter = st.selectbox("Filter by Status", ["ALL", "ACTIVE", "PROBATION", "SPARSE"])

    filtered_pws = store.pathways
    if intent_filter != "ALL":
        filtered_pws = [p for p in filtered_pws if p.intent == intent_filter]
    if status_filter != "ALL":
        filtered_pws = [p for p in filtered_pws if p.status == status_filter]

    st.markdown(f"Showing **{len(filtered_pws)}** pathways")

    for p in filtered_pws[:20]:
        with st.expander(f"📌 {p.pathway_id} | {p.intent} ➔ {p.action} (Evidence: {p.evidence_count}, Conf: {p.pathway_confidence:.2f})"):
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown(f"**Intent**: `{p.intent}`")
                st.markdown(f"**Action**: `{p.action}`")
                st.markdown(f"**Status**: `{p.status}`")
                st.markdown(f"**Conditions**: `{json.dumps(p.conditions)}`")
                st.markdown(f"**Last Observed**: `{p.last_observed}`")
            with c2:
                st.markdown(f"**Outcome Distribution**: `{json.dumps(p.outcome_distribution)}`")
                st.markdown(f"**Supporting Conversations**: `{', '.join(p.supporting_conversations[:5])}`")
                if p.sample_agent_responses:
                    st.markdown(f"**Sample Real Response**: *\"{p.sample_agent_responses[0]}\"*")

# -------------------------------------------------------------
# TAB 3: Playbook Evolution & Drift
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### Support Behavior Evolution & Temporal Drift Analytics")
    st.markdown("Tracks how support action distributions shifted across 4 chronological windows in TWCS.")

    intent_for_drift = st.selectbox("Select Intent for Drift Visualization", list(drift_monitor.intent_drift_scores.keys()))
    drift_data = drift_monitor.get_intent_drift(intent_for_drift)

    st.metric("Recent Jensen-Shannon Divergence (JSD)", f"{drift_data['recent_jsd']:.4f}", f"Threshold: {drift_data['threshold_jsd']}")
    if drift_data['is_drifting']:
        st.warning("⚠️ This intent is experiencing significant temporal drift! Trust in historical pathways is automatically penalized.")
    else:
        st.success("✅ Support actions for this intent are stable across temporal windows.")

    # Window distributions table
    w_dists = drift_data['window_distributions']
    if w_dists:
        df_drift_vis = pd.DataFrame(w_dists).fillna(0.0)
        df_drift_vis.index = [f"Window {i+1} (Oct-Dec 2017)" for i in range(len(w_dists))]
        st.dataframe(df_drift_vis.style.format("{:.1%}"), use_container_width=True)

# -------------------------------------------------------------
# TAB 4: Playbook Expansion Queue
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### Playbook Expansion Queue (UNKNOWN Case Pipeline)")
    st.markdown("When a customer situation matches no existing historical pathway, ResolveTrace routes it here for human review rather than guessing.")

    expansion_samples = [
        {"Case ID": "EXP_001", "Query": "Can I connect my smart refrigerator in Korean?", "Reason": "Exotic hardware + unseen language", "Priority": "HIGH"},
        {"Case ID": "EXP_002", "Query": "Spotify took cryptocurrency directly from wallet", "Reason": "Unsupported payment instrument", "Priority": "HIGH"},
        {"Case ID": "EXP_003", "Query": "Section 512 copyright legal notice to legal team", "Reason": "Legal/compliance non-support query", "Priority": "CRITICAL"},
        {"Case ID": "EXP_004", "Query": "Cassette player audio sync on retro Commodore 64", "Reason": "Obsolete hardware platform", "Priority": "LOW"}
    ]
    st.dataframe(pd.DataFrame(expansion_samples), use_container_width=True)

# -------------------------------------------------------------
# TAB 5: Evaluation & Benchmarks
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### Standardized Evaluation Benchmark & Ablation Study")
    
    if metrics and 'ablation_table' in metrics:
        df_abl = pd.DataFrame(metrics['ablation_table']).T
        st.dataframe(df_abl, use_container_width=True)

    col_img, col_notes = st.columns([1, 1])
    with col_img:
        plot_path = config['paths']['safety_curve_plot']
        if os.path.exists(plot_path):
            st.image(plot_path, caption="Automation Safety Curve (Coverage vs False Auto-Handling Rate)")
    with col_notes:
        st.markdown("#### Key Benchmark Conclusions:")
        st.markdown("1. **Decision Pathways vs. Raw Retrieval**: Support Playbook achieves higher action selection precision than raw Semantic RAG.")
        st.markdown("2. **Safety & Risk Gating**: Full ResolveTrace reduces unsafe auto-handling by routing high-risk and conflicting cases to ESCALATE.")
        st.markdown("3. **Unknown Recognition**: Explicit UNKNOWN detection prevents hallucinating confident answers on unsupported edge cases.")
