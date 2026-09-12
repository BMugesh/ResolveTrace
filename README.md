# ResolveTrace — Historical Support Playbook (SpotifyCares)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests: Passing](https://img.shields.io/badge/Tests-23%20Passed-brightgreen.svg)](tests/)

> **ResolveTrace** extracts, validates, and operationalizes historical customer support decision pathways from the Customer Support on Twitter (TWCS) dataset for **SpotifyCares**. Instead of blindly copying historical replies, ResolveTrace learns:  
> **Customer Situation (Intent + State) $\rightarrow$ Support Decision (Action) $\rightarrow$ Outcome Distribution + Evidence**

---

## Key Highlights & Results

* **Brand**: `SpotifyCares` (91,081 filtered tweets, 28,187 reconstructed threads)
* **Playbook**: **1,545 mined pathways** (297 ACTIVE, 323 PROBATION, 925 SPARSE) with Bayesian Laplace-shrunk confidence
* **Decisions**: 3-Way Safety Gating (`AUTO-HANDLE`, `ESCALATE`, `UNKNOWN`)
* **Conflict & Unknown Detection**: Conflict margin $\delta = 0.08$, Unknown threshold $\tau = 0.50$
* **Temporal Drift**: Rolling-window Jensen-Shannon Divergence ($D_{JS}$) monitoring
* **Evaluations**: Benchmark comparing 7 systems across Intent F1, Pathway Accuracy, Safety, and LLM Judge Rubric Quality

---

## Complete Ablation Benchmark

| System | Intent Macro-F1 | Pathway Accuracy | Unknown F1 | Conflict F1 | Reply Quality (Human / LLM) | False Auto-Handling Rate | Automation Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Majority Baseline** | 0.014 | — | — | — | — | — | — |
| **TF-IDF + Logistic Regression** | **0.764** | — | — | — | — | — | — |
| **Semantic RAG** | — | 0.531 | 0.000 | 0.000 | 4.40 / 4.62 | 9.7% | 100.0% |
| **Semantic RAG + Intent** | 0.764 | 0.536 | 0.000 | 0.000 | 4.45 / 4.72 | 9.7% | 100.0% |
| **Support Playbook (Vanilla)** | 0.764 | 0.604 | 0.000 | 0.000 | 4.48 / 4.73 | 9.7% | 100.0% |
| **+ Conflict & Unknown** | 0.764 | 0.604 | 0.424 | 0.820 | 4.50 / 4.81 | 4.3% | 68.1% |
| **ResolveTrace (Full System)** | **0.764** | **0.604** | **0.424** | **0.880** | **4.50** / **4.85** | **4.3%** | **67.2%** |

---

## Reproduce in Under 15 Minutes

> **⚡ Fast path**: Use `--sample` flag in Step 3 to run on 500 threads in ~4 minutes without downloading the full dataset.

### 0. Download the Dataset
The raw dataset is not included in the repo (too large for GitHub). Download the **Customer Support on Twitter (TWCS)** dataset from Kaggle:

```
https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter
```

Place the downloaded files in the project root:
```
ResolveTrace/
├── spotify_cares_filtered_threads.csv   ← from dataset
├── spotify_cares_turn_structure.csv     ← from dataset
```

> **Skip this step** if you only want to explore: pre-built deliverables (`artifacts/playbook.json`, `artifacts/metrics.json`, `data/golden/golden_set.csv`) are already committed and ready to inspect.

### 1. Setup Environment
```bash
git clone https://github.com/BMugesh/ResolveTrace.git
cd ResolveTrace
pip install -r requirements.txt
```

### 2. Inspect Dataset (Phase 0)
```bash
python scripts/inspect_dataset.py
```
*Outputs: `artifacts/dataset_stats.json`, `artifacts/dataset_report.md`*

### 3. Build Processed Dataset & Temporal Splits (Phases 1-3)
```bash
# Full dataset mode (28,187 threads)
python scripts/build_dataset.py

# Or fast sample mode (500 threads, ~1 min)
python scripts/build_dataset.py --sample
```

### 4. Build Support Playbook & Mine Pathways (Phases 4-9)
```bash
python scripts/build_playbook.py
```
*Outputs: `artifacts/playbook.json`, `artifacts/pathway_metrics.json`*

### 5. Generate Golden Benchmark & Drift Challenge Set (Phases 15-16)
```bash
python scripts/create_golden_set.py
```

### 6. Run Complete Benchmark Evaluation & Ablation Suite (Phase 17)
```bash
python scripts/evaluate.py
```
*Outputs: `artifacts/metrics.json`, `artifacts/figures/automation_safety_curve.png`*

### 7. Run Interactive CLI Demonstration
```bash
python scripts/run_demo.py
```

### 8. Run Unit Tests (23 tests across 8 test suites)
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### 9. Launch Streamlit Web Dashboard & Playbook Explorer
```bash
streamlit run app/ui.py
```

### 10. Launch FastAPI Backend
```bash
uvicorn app.api:app --reload --port 8000
```

---

## Repository Structure

```
resolvetrace/
├── README.md                          # Quickstart (<15 min reproduction), system overview
├── report.md                          # Comprehensive technical report (<=6 pages)
├── decision_log.md                    # 15 non-obvious engineering decisions
├── requirements.txt                   # Project dependencies
├── .env.example                       # Environment configuration
│
├── configs/
│   ├── config.yaml                    # System paths and configuration
│   ├── taxonomy.yaml                  # Frozen 12-intent SpotifyCares taxonomy
│   └── thresholds.yaml                # Calibrated decision thresholds (delta, tau, auto)
│
├── data/
│   ├── sample/                        # Quick-inspection CSV sample
│   ├── processed/                     # Train/Val/Test temporal JSONL splits
│   └── golden/
│       ├── golden_set.csv             # 207-case stratified golden benchmark
│       ├── drift_challenge_set.csv    # 35-case temporal drift challenge set
│       └── ANNOTATION_GUIDE.md        # Comprehensive ground truth annotation guide
│
├── artifacts/
│   ├── dataset_stats.json             # Machine-readable dataset inspection stats
│   ├── dataset_report.md              # Human-readable dataset inspection report
│   ├── playbook.json                  # Complete mined Support Playbook (1,545 pathways)
│   ├── pathway_metrics.json           # Pathway confidence and audit metrics
│   ├── metrics.json                   # Full benchmark evaluation output
│   └── figures/
│       └── automation_safety_curve.png # Automation Coverage vs False Auto-Handling Curve
│
├── src/
│   ├── data/                          # Reconstruction, loader, and temporal splitting
│   ├── taxonomy/                      # Taxonomy schema and rule-based classifier
│   ├── classification/                # Majority and TF-IDF Logistic Regression baselines
│   ├── state/                         # Customer situation state extraction & evidence
│   ├── resolution/                    # Action extraction, outcome inference, audit
│   ├── playbook/                      # Playbook schema, builder, store, and matcher
│   ├── retrieval/                     # Semantic RAG baseline retriever
│   ├── conflict/                      # Operational strategy conflict detector
│   ├── drift/                         # JSD rolling-window drift monitor
│   ├── risk/                          # Domain risk classifier (LOW, MEDIUM, HIGH)
│   ├── decision/                      # 3-way decision engine (AUTO-HANDLE, ESCALATE, UNKNOWN)
│   ├── generation/                    # Grounded response generator
│   └── evaluation/                    # Benchmarking, LLM judge, and metrics
│
├── app/
│   ├── api.py                         # FastAPI REST endpoints
│   └── ui.py                          # Streamlit interactive web dashboard
│
├── scripts/
│   ├── inspect_dataset.py             # Phase 0 dataset inspection
│   ├── build_dataset.py               # Dataset construction and temporal splits
│   ├── build_playbook.py              # Playbook mining and audit
│   ├── create_golden_set.py           # Golden benchmark creation
│   ├── evaluate.py                    # 7-system benchmark evaluation
│   └── run_demo.py                    # 3-case CLI interactive demo
│
└── tests/                             # Unit tests (19 tests)
```

---

## Core System Concepts

### 1. Customer Situation State
ResolveTrace extracts a structured state vector for every customer message:
```json
{
  "info_provided": true,
  "troubleshoot_attempted": false,
  "issue_recurring": true,
  "billing_related": false,
  "device_type": "Android",
  "sentiment_frustrated": true,
  "evidence": {
    "device_type": "android tablet",
    "issue_recurring": "keeps skipping"
  }
}
```

### 2. Support Playbook Pathway
Atomic unit representing historical organizational knowledge:
```json
{
  "pathway_id": "PW_PLAY_0976",
  "intent": "PLAYBACK_STREAMING_AUDIO",
  "conditions": {
    "info_provided": true,
    "troubleshoot_attempted": false,
    "issue_recurring": true,
    "billing_related": false,
    "device_type": "Android"
  },
  "action": "PROVIDE_INSTRUCTIONS",
  "outcome_distribution": {
    "RESOLVED": 42,
    "LIKELY_RESOLVED": 58,
    "UNRESOLVED_OPEN": 24
  },
  "evidence_count": 124,
  "pathway_confidence": 0.83,
  "status": "ACTIVE"
}
```

### 3. Three-Way Decision Gating
* **`AUTO-HANDLE`**: Strong pathway ($C_p \ge 0.55$), high match score, no conflict, low risk, low drift, composite automation score $\ge 0.55$.
* **`ESCALATE`**: Pathway exists, but high risk, strategy conflict ($P_1 - P_2 < \delta = 0.08$), or recent drift requires human specialist handling.
* **`UNKNOWN`**: No reliable historical pathway (score $< \tau = 0.50$ or unmapped domain). Case is routed to the **Playbook Expansion Queue** for human review and new pathway creation.

---

## Golden Evaluation Benchmark ($N=207$) & Annotation Standards

* **Sampling & Stratification**: 207 frozen test cases sampled across common intents (`SUBSCRIPTION_BILLING_PREMIUM`, `PLAYBACK_STREAMING_AUDIO`, `PLAYLIST_LIBRARY_CATALOG`, `ACCOUNT_ACCESS_AUTH`), mid-volume technical intents, and long-tail intents (`ARTIST_CONTENT_INQUIRY`, `AMBIGUOUS_INQUIRY`), with 138 Low, 64 Medium, and 5 High risk scenarios.
* **Labelling Methodology**: Hybrid protocol where candidate held-out conversations were pre-annotated with rule-based heuristics and manually verified and reconciled against [`data/golden/ANNOTATION_GUIDE.md`](data/golden/ANNOTATION_GUIDE.md).
* **Pathway Evidence Breakdown**: Stratified evaluation reveals **69.5% accuracy on ACTIVE pathways** ($N \ge 4$, Conf $\ge 0.55$), **51.5% on PROBATION pathways** ($N \ge 4$, Conf $< 0.55$), and **61.5% on SPARSE pathways** ($N < 4$, $n=13$), summing to $95 + 99 + 13 = \mathbf{207}$ test cases.
