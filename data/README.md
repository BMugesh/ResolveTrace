# ResolveTrace — Data Directory Documentation

This directory contains the processed data splits, samples, and golden evaluation benchmark for **SpotifyCares** derived from the Customer Support on Twitter (TWCS) dataset (`twcs/twcs.csv`).

---

## Directory Structure

* **`sample/`**:
  * `sample_spotify_threads.csv`: A lightweight CSV subset of 100 threads (342 rows) for fast testing and continuous integration without loading the multi-gigabyte TWCS corpus.
* **`processed/`**:
  * `spotify_conversations.jsonl`: Full reconstructed conversation corpus for SpotifyCares (28,187 conversation threads, 91,081 turns).
  * `train_conversations.jsonl`: Chronological Train split (older 70%, 19,730 conversations).
  * `val_conversations.jsonl`: Chronological Validation split (middle 15%, 4,228 conversations).
  * `test_conversations.jsonl`: Chronological Test split (latest 15%, 4,229 conversations).
* **`golden/`**:
  * `golden_set.csv`: 207 hand-labeled, stratified gold test cases covering common intents, rare intents, high-risk security disputes, pathway conflicts, and unmapped edge cases (reconciled ground truth).
  * `golden_set_prereconciliation.csv`: Historical pre-reconciliation archive of the 207 cases before the 12 manual review overrides were applied; retained strictly for provenance and audit trail purposes (not loaded by any evaluation scripts).
  * `drift_challenge_set.csv`: 35 targeted temporal drift challenge cases.
  * `ANNOTATION_GUIDE.md`: Comprehensive ground truth annotation definitions, inclusion/exclusion criteria, and decision standards.

---

## Split Strategy & Leakage Prevention
* **Unit of Splitting**: Whole conversation threads.
* **Guarantee**: Zero individual tweets or turns from the same conversation leak across train, validation, or test sets.
* **Temporal Ordering**: Conversations are strictly sorted by opening timestamp ($T_0$) to simulate realistic production deployment where historical knowledge predicts future tickets.
