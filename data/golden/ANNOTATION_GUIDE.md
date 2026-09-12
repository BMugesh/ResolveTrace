# ResolveTrace — Golden Evaluation Set Annotation Guide

This guide establishes the ground truth labeling standards, taxonomy definitions, and decision criteria used to construct and evaluate the **ResolveTrace Golden Benchmark** (`data/golden/golden_set.csv`, 207 cases) and **Drift Challenge Set** (`data/golden/drift_challenge_set.csv`, 35 cases).

---

## 1. Intent Taxonomy Standards

| Intent Category | Criteria & Inclusion Boundaries | Common Ambiguities & Disambiguation |
| :--- | :--- | :--- |
| `SUBSCRIPTION_BILLING_PREMIUM` | Payment failures, charges, invoice queries, refund requests, premium renewal. | If customer mentions student status, label as `STUDENT_DISCOUNT_HULU`. If family member invite, label as `FAMILY_PLAN_SETUP`. |
| `STUDENT_DISCOUNT_HULU` | SheerID verification, student discount expiration, bundled Hulu/Showtime activation. | Only applies when student plan or bundled partner is specifically mentioned. |
| `FAMILY_PLAN_SETUP` | Adding/inviting members, address verification errors (Error Code 3), family manager setup. | Excludes generic billing disputes regarding monthly cost. |
| `ACCOUNT_ACCESS_AUTH` | Forgotten passwords, hacked/compromised credentials, unauthorized email changes. | If account is accessible and issue is payment, classify as `SUBSCRIPTION_BILLING_PREMIUM`. |
| `PLAYBACK_STREAMING_AUDIO` | Active track playback failing, skipping after seconds, buffering, silence, audio crackling. | Excludes offline download failures (see `OFFLINE_SYNC_DOWNLOADS`) and Bluetooth pairing issues (see `DEVICE_INTEGRATION_CONNECT`). |
| `OFFLINE_SYNC_DOWNLOADS` | Downloaded songs disappearing, sync stuck at 0%, local files missing or unplayable offline. | Excludes online streaming buffering. |
| `APP_CRASH_BUG` | Sudden app crash to desktop/home screen, black blank screen, unresponsive frozen UI. | Excludes audio stuttering if app remains responsive. |
| `PLAYLIST_LIBRARY_CATALOG` | Missing songs, greyed-out tracks, playlist organization, search results, library sorting. | Inquiries by artists uploading music belong to `ARTIST_CONTENT_INQUIRY`. |
| `DEVICE_INTEGRATION_CONNECT` | Spotify Connect, Bluetooth speaker pairing, smart speakers (Alexa, Google Home, Sonos), car audio (CarPlay). | Built-in phone speaker playback belongs to `PLAYBACK_STREAMING_AUDIO`. |
| `ARTIST_CONTENT_INQUIRY` | Music distribution, Spotify for Artists profile, aggregator submission, track metadata. | Listener inquiries about songs belong to `PLAYLIST_LIBRARY_CATALOG`. |
| `GENERAL_INQUIRY_FEEDBACK` | Feature requests, UI comments, general questions, tablet mode support inquiries. | General fallback for inquiries that do not describe technical failure. |
| `AMBIGUOUS_INQUIRY` | Extremely sparse tweets (<3 words, e.g. "@SpotifyCares help"), gibberish, uninterpretable media. | Used when no problem category can be honestly inferred. |

---

## 2. Customer State Variables

* `info_provided`: Boolean indicating whether customer provided actionable diagnostic context (device model, OS/app version, error message, or symptom description).
* `troubleshoot_attempted`: Boolean indicating whether customer explicitly stated trying prior troubleshooting (e.g. "already restarted", "reinstalled the app", "cleared cache").
* `issue_recurring`: Boolean indicating whether problem is persistent or repeated ("still happening", "keeps skipping", "happens every day").
* `billing_related`: Boolean indicating involvement of payment, monetary charge, bank account, or subscription invoice.
* `device_type`: Controlled vocabulary: `iPhone`, `iPad`, `Mac`, `Apple Watch`, `Apple TV`, `Android`, `Windows/PC`, `Audio/Accessory`, `Smart TV/Console`, or `unknown`.

---

## 3. Agent Action Vocabulary

* `REQUEST_INFO_AND_REDIRECT_DM`: Agent asks for specific diagnostic details and simultaneously provides a direct link to private Direct Message.
* `REQUEST_INFORMATION`: Agent asks diagnostic probing questions (device model, OS version, reproduction steps).
* `PROVIDE_INSTRUCTIONS`: Agent provides step-by-step navigation, settings toggles, or official documentation link.
* `REDIRECT_DM`: Agent directly asks customer to transition to private DM.
* `PROVIDE_GENERAL_ASSISTANCE`: Agent offers general support or acknowledges customer feedback.
* `ESCALATE_INTERNAL`: Agent escalates to backstage specialists or engineering team.
* `CONFIRM_RESOLUTION`: Agent verifies fix or acknowledges positive customer feedback.
* `CLOSING_COURTESY`: Agent sends polite sign-off ("You're welcome!", "Have a great day!").
* `TROUBLESHOOT_REINSTALL`: Agent instructs clean app reinstallation.
* `TROUBLESHOOT_UPDATE`: Agent instructs app or OS update to latest version.
* `TROUBLESHOOT_RESTART`: Agent instructs device reboot or power cycle.
* `EXPLAIN_POLICY_OR_CATALOG`: Agent explains music licensing agreements or catalog rights.

---

## 4. Inferred Outcome Categories

1. `RESOLVED`: Explicit customer confirmation of successful issue resolution (e.g. "thanks that fixed it", "working now!").
2. `LIKELY_RESOLVED`: Agent provided substantive instructions/guidance and customer acknowledged with appreciation without reporting further issue.
3. `ESCALATED`: Interaction moved to private Direct Message or internal backstage team.
4. `UNRESOLVED_OPEN`: Conversation ended or trailed off without resolution confirmation or explicit escalation.

---

## 5. Decision Space

* `AUTO-HANDLE`: Pathway is strong, confidence is high, evidence is sufficient, no conflict, low/medium risk, low drift.
* `ESCALATE`: A pathway exists, but high risk, pathway conflict, insufficient evidence, high drift, or low confidence makes autonomous handling unsafe.
* `UNKNOWN`: No sufficiently reliable historical pathway exists. Case is routed to the **Playbook Expansion Queue** for human specialist review and new pathway creation.
