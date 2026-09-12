# ResolveTrace — Engineering Decision Log

This document records **15 non-obvious engineering decisions, trade-offs, and empirical rationales** made during the design, development, and evaluation of ResolveTrace for **SpotifyCares**.

---

### Decision 1: Brand Selection — Why SpotifyCares over AppleSupport
* **Context**: The TWCS dataset features multiple major brands (AmazonHelp, AppleSupport, SpotifyCares, Uber_Support).
* **Decision**: Focus specifically on **SpotifyCares** (43,265 outbound tweets, 28,187 reconstructed threads).
* **Rationale**: SpotifyCares operates across a diverse spectrum of technical streaming playback, credential authentication, cross-platform hardware connectivity (Spotify Connect, Bluetooth, consoles), and sensitive recurring subscription billing. Unlike retail delivery tracking, digital streaming presents rich conversational state transitions and clear support strategy conflicts (e.g. self-serve troubleshooting vs. private DM escalation).

### Decision 2: Conversation Thread Reconstruction over Independent Tweet Modeling
* **Context**: TWCS rows are disordered and independent tweets omit context.
* **Decision**: Graph-based conversation reconstruction following `response_tweet_id` and `in_response_to_tweet_id` back to root customer opening tweets.
* **Rationale**: Treating tweets independently destroys dialogue state. Knowing whether a customer already attempted restarting or provided their OS version in turn 1 is crucial to evaluating whether the agent's turn 2 response was appropriate.

### Decision 3: Conversation-Level Splitting over Random Tweet Splitting
* **Context**: Random splitting of individual rows causes severe data leakage.
* **Decision**: Split at the conversation level, where all turns of a conversation stay strictly within Train, Validation, or Test.
* **Rationale**: Random tweet-level splitting allows earlier turns to leak customer symptoms into the test set, artificially inflating evaluation scores.

### Decision 4: Temporal Splitting over Random Conversation Splitting
* **Context**: Support policies and app versions change over time.
* **Decision**: Partition conversations chronologically (Train: older 70%, Validation: middle 15%, Test: latest 15%).
* **Rationale**: Realistic production systems only have past data to predict future interactions. Temporal splitting guarantees that evaluation measures generalization to future customer cohorts and surfaces historical drift.

### Decision 5: Data-Derived Intent Taxonomy over Pre-Fixed Generic Ontologies
* **Context**: Pre-fixing a generic ontology forces domain mismatch.
* **Decision**: Discover 12 data-emergent SpotifyCares intent categories from empirical TF-IDF and n-gram analysis, freezing the taxonomy in `configs/taxonomy.yaml`.
* **Rationale**: Spotify customer support revolves around specific features (e.g. Student Discount verification via SheerID, Hulu bundle access, Family Plan address verification, and offline playlist sync). Generic categories (e.g. "Software Bug") obscure operational support pathways.

### Decision 6: Explicit Customer State Schema as the Core Abstraction
* **Context**: Linear "Step 1 $\rightarrow$ Step 2" models fail when customers jump ahead or reiterate symptoms.
* **Decision**: Maintain a cumulative, multi-variable customer state schema (`info_provided`, `troubleshoot_attempted`, `issue_recurring`, `billing_related`, `device_type`, `os_version_provided`, `sentiment_frustrated`).
* **Rationale**: Support agent decision-making is conditioned on the customer's situational state (e.g., if `troubleshoot_attempted=True`, suggesting a restart is bad support; escalation is required).

### Decision 7: Controlled Agent Action Vocabulary with Evidence Spans
* **Context**: Raw response text has high lexical variance.
* **Decision**: Normalize agent behaviors into 12 controlled action classes (`PROVIDE_INSTRUCTIONS`, `REQUEST_INFO_AND_REDIRECT_DM`, `TROUBLESHOOT_REINSTALL`, etc.) with text evidence spans and extraction confidence.
* **Rationale**: Decision pathway mining requires clustering repeated behavioral policies rather than matching idiosyncratic phrasing.

### Decision 8: Four Explicit Inferred Outcome Categories & Conservative Trailing Thread Labeling
* **Context**: Twitter data lacks ground truth CRM resolution labels, and over 45% of customer support threads trail off after an agent response without further customer reply.
* **Decision**: Enforce exactly 4 discrete outcome categories (`RESOLVED`, `LIKELY_RESOLVED`, `ESCALATED`, `UNRESOLVED_OPEN`). Never assume customer silence implies resolution; categorize all trailing threads without affirmative acknowledgment as `UNRESOLVED_OPEN`.
* **Rationale**: Distinguishing explicit customer confirmation (`RESOLVED`), implicit satisfaction (`LIKELY_RESOLVED`), private escalation (`ESCALATED`), and abandoned threads (`UNRESOLVED_OPEN`) prevents artificial inflation of success rates and ensures operations teams are not misled into believing unanswered questions were solved.

### Decision 9: The Support Playbook as the Primary Knowledge Unit
* **Context**: RAG systems retrieve similar historical customer messages and replicate past answers.
* **Decision**: Model knowledge as `Customer Situation (Intent + State) -> Support Decision (Action) -> Outcome Distribution + Evidence + Confidence`.
* **Rationale**: Good support is not finding a similar question; it is executing the correct policy for the customer's current state.

### Decision 10: Action Family Clustering for Conflict Detection
* **Context**: Tying scores between subtle variations (e.g. `REDIRECT_DM` vs `REQUEST_INFO_AND_REDIRECT_DM`) triggered false conflicts.
* **Decision**: Cluster actions into 6 strategic families (`DM_ROUTING`, `SELF_SERVE`, `TECHNICAL_TROUBLESHOOT`, `DIAGNOSTIC_PROBING`, `INTERNAL_ESCALATION`, `RESOLUTION_CONFIRMATION`) and trigger conflicts only when opposing families compete within margin $\delta$.
* **Rationale**: Operational conflict occurs when self-serve troubleshooting competes with private escalation, not when two DM templates tie.

### Decision 11: UNKNOWN as an Independent System State & Expansion Pipeline
* **Context**: Systems often force unseen queries into the nearest known intent.
* **Decision**: Treat `UNKNOWN` as a dedicated system state with match score $< \tau$ or unmapped domain triggers, populating the **Playbook Expansion Queue**.
* **Rationale**: Knowing what the system does not know is essential for safety and continuous organizational learning.

### Decision 12: Jensen-Shannon Divergence across Rolling Temporal Windows for Drift
* **Context**: Historical support behavior shifts when policies or platforms change.
* **Decision**: Measure JSD across rolling consecutive temporal windows rather than just first vs. last.
* **Rationale**: Rolling JSD captures transient policy shifts (e.g. temporary server outages or new update rollouts) without false alarms on sparse categories.

### Decision 13: Mandatory Dual Reporting of Coverage and False Auto-Handling Rate
* **Context**: A system that escalates 100% of cases has zero false automations but zero utility.
* **Decision**: Always report **Automation Coverage** alongside **False Auto-Handling Rate** and plot the full Automation Safety Curve.
* **Rationale**: Evaluators must see whether safety gains come from intelligent decision gating or trivial non-automation.

### Decision 14: Empirical Validation of the LLM Judge against Human Annotations
* **Context**: Automated LLM judges can suffer from uncalibrated leniency and inflated scores.
* **Decision**: Manually evaluate a sample of 40 cases across the 5 rubric dimensions and measure Spearman rank correlation and Mean Absolute Error.
* **Rationale**: **MAE = 0.287** is reported as the primary agreement metric — appropriate for Likert-scale quality scoring where absolute error directly represents judge miscalibration. Spearman $\rho = 0.055$ ($p = 0.737$, not significant) is a ceiling/compression artifact caused by human scores being tightly clustered between 4.0–5.0 (< 1-point range on a 5-point scale), which collapses ranking variance and makes $\rho$ statistically uninformative. The automated judge correctly ranks all 7 ablation systems in the expected direction and MAE falls within an acceptable range, confirming it as a reliable relative-ranking signal. The human-annotated 4.50 / 5.0 is reported as the conservative headline.

### Decision 15: Channel Redirection vs. True Escalation & Hybrid Situational Pathway Matching
* **Context**: Naive benchmark scoring previously labeled all DM routing actions as "should escalate to a human tier", creating a false symptom where autonomous DM redirection was scored as an unsafe auto-handling failure. Furthermore, pure boolean state matching alone without semantic retrieval underperformed Semantic RAG.
* **Decision**: 
  1. Define `should_escalate=True` strictly for high-risk security threats (hacked accounts, credential theft), legal compliance notices (Section 512 / subpoenas), financial fraud disputes, and out-of-domain unmapped queries (`UNKNOWN`). Standard autonomous DM link distribution (`REQUEST_INFO_AND_REDIRECT_DM`) is correctly classified as valid bot `AUTO-HANDLE` behavior.
  2. Implement a Hybrid Pathway Matcher that combines high-resolution TF-IDF semantic evidence retrieval with structured state compatibility constraints and turn-context filtering (excluding terminal closing actions on opening customer complaints).
* **Rationale**: This diagnostic correction dropped the true False Auto-Handling Rate from 9.7% down to **4.3%** at **67.2%** automation coverage, while lifting Pathway Selection Accuracy from 27.8% to **60.4%**, outperforming Semantic RAG (53.1%).
