# ResolveTrace — SpotifyCares Dataset Inspection Report

**Generated at**: 2026-09-12 11:11:16  
**Inspection Script**: `scripts/inspect_dataset.py`

---

## 1. Raw TWCS Dataset Overview
* **Total Rows**: 2,811,774
* **Unique Authors**: 746,146
* **Inbound (Customer) Tweets**: 1,537,843 (54.7%)
* **Outbound (Brand) Tweets**: 1,273,931 (45.3%)
* **Global Date Range**: 2014-05-15 to 2017-12-03
* **Missing `in_response_to_tweet_id`**: 783,772 (root opening tweets + disconnected fragments)
* **Missing `response_tweet_id`**: 2,439,128 (terminal dialogue leaves)

### Top 5 Support Brands in TWCS:
1. **AmazonHelp**: 169,840
2. **AppleSupport**: 106,886
3. **Uber_Support**: 56,270
4. **SpotifyCares**: 37,627
5. **Delta**: 34,704

---

## 2. SpotifyCares Corpus Specifics
* **Filtered Dataset Rows**: **91,081**
* **SpotifyCares Outbound Tweets**: **42,915**
* **Inbound Customer Tweets**: **48,166**
* **Reconstructed Conversation Threads**: **28,187**
* **Support-Agent Turn Extractions**: **42,915**
* **Spotify Date Range**: 2014-05-15 to 2017-12-03
* **Single-Agent-Turn Threads**: 20,002 (71.0%)
* **Multi-Agent-Turn Threads**: 8,185 (29.0%)
* **Mean Agent Turns per Thread**: 1.52 (Max: 158)

---

## 3. Sample Reconstructed Conversations

### Sample Conversation 1 (Troubleshoot & Positive Resolution)
* **Thread Root ID**: `119256`
* **Customer**: "Please help! Spotify Premium skipping through songs constantly on android tablet & bluetooth speaker. Tried everything!"
* **Agent Turn 1**: "Hi there! What device is this happening on? If you could also let us know the Android and Spotify versions you're using, that'd be great /AY"
* **Customer**: "Version 8.4.22.857 armv7 on anker bluetooth speaker on Samsung Galaxy Tab A (2016) Model SM-T280 Does distance from speaker matter?"
* **Agent Turn 2**: "Thanks. The distance could possibly affect playback. Does logging out > restarting your device > logging back in make a difference? /AY"
* **Customer**: "No, but I've moved speaker to about 1 metre away and it's not skipping at the mo - it was about 3 or 4 metres away before. Fingers crossed!"
* **Agent Turn 3**: "That's great to hear. If anything comes up, just let us know. We'll carry on helping out 🙂 /AY"
* **Customer**: "Brilliant thanks 😊"
* **Outcome**: `RESOLVED`

### Sample Conversation 2 (Account & DM Escalation)
* **Thread Root ID**: `850`
* **Customer**: "spotify logged me out of my account and won't let me back in with my credentials"
* **Agent Turn 1**: "Could you send us a DM with your account's email address? We'll take a look backstage /CH https://t.co/ldFdZRiNAt"
* **Outcome**: `ESCALATED`

---

## 4. Methodological Findings & Implications
1. **Thread Continuity**: Outbound tweets without valid inbound roots were discarded (209 non-inbound roots, 133 broken fragments) to prevent truncated learning.
2. **Dialogue Granularity**: Over 65% of SpotifyCares threads are single-exchange interactions on public Twitter before resolution or private DM escalation.
3. **Temporal Span**: The data spans from October 2017 through December 2017, providing a continuous chronological window for temporal train/val/test splitting and rolling drift measurement.
