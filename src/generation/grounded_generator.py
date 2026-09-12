import os
import re
import json
import time
import requests
from typing import Dict, Any, List, Optional, Tuple, Union
from src.state.schema import CustomerState
from src.evaluation.llm_judge import LLMJudge

# Auto-load .env if present
if os.path.exists('.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv('.env', override=True)
    except ImportError:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k.strip()] = v.strip()

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "groq/compound-mini")
GROQ_TIMEOUT_SECONDS = 8
_groq_session = requests.Session()

def call_groq(prompt: str, temperature: float = 0.2, max_tokens: int = 120) -> dict:
    """
    Calls Groq's chat completion API. Returns a dict with either
    {'success': True, 'text': ..., 'latency_ms': ...} or
    {'success': False, 'error': ...} — never raises, so the caller
    can always fall back to the deterministic template path.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return {"success": False, "error": "GROQ_API_KEY not set"}

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    # Try configured model, fallback to compound-mini if model is unavailable
    models_to_try = [GROQ_MODEL] if GROQ_MODEL == "groq/compound-mini" else [GROQ_MODEL, "groq/compound-mini"]

    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a professional, helpful, concise customer support agent for SpotifyCares on Twitter. You adhere strictly to evidence-based policy."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        start = time.monotonic()
        try:
            res = _groq_session.post(GROQ_API_URL, json=payload, headers=headers, timeout=GROQ_TIMEOUT_SECONDS)
        except requests.RequestException as e:
            return {"success": False, "error": f"request_failed: {e}"}
        latency_ms = int((time.monotonic() - start) * 1000)

        if res.status_code == 200:
            try:
                text = res.json()["choices"][0]["message"]["content"].strip()
                return {"success": True, "text": text, "latency_ms": latency_ms, "model": model_name}
            except (KeyError, IndexError, ValueError) as e:
                return {"success": False, "error": f"parse_failed: {e}"}
        elif res.status_code == 404 and model_name != "groq/compound-mini":
            continue
        else:
            return {"success": False, "error": f"http_{res.status_code}: {res.text[:200]}"}

    return {"success": False, "error": "no_available_models"}


class GroundedResponseGenerator:
    """
    Generates customer support responses strictly grounded in:
      - Selected historical pathway
      - Approved support action
      - Extracted customer state
      - Authentic historical agent response templates & evidence
    
    Guardrails:
      1. Pre-call Sanitization: Strips handles and personal identifiers before API calls.
      2. Post-generation LLM-Judge Check: Validates groundedness and safety before output.
      3. Low Temperature (0.2): Ensures consistent, reproducible outputs.
      4. Artifact Logging: Logs every prompt + response to artifacts/generation_logs.jsonl.
      5. AUTO-HANDLE Only: Skips customer reply generation for ESCALATE and UNKNOWN.
    """

    PROMPT_TEMPLATE = """You are drafting a SpotifyCares support reply. You must ONLY use the
approved action and evidence below — do not invent policies, promises,
timelines, or outcomes not supported by the evidence.

Customer message: {customer_text}
Detected intent: {intent}
Matched historical action: {action}          # e.g. TROUBLESHOOT_RESTART
Evidence (past similar cases, sanitized):
{evidence_snippets}                          # 2-3 real past agent replies for this pathway

Write a single, natural-sounding reply that carries out the action above.
Do not mention refunds, specific timeframes, or guarantees unless they
appear in the evidence. Keep it under 280 characters, in SpotifyCares' tone."""

    ACTION_TEMPLATES = {
        'PROVIDE_INSTRUCTIONS': {
            'OFFLINE_SYNC_DOWNLOADS': "Hey there! To clear your cache on iPhone: open Spotify > tap Settings (⚙️) > Storage > Clear Cache. To re-download your playlist, make sure you're on WiFi and toggle Download on the playlist page! /SC",
            'PLAYBACK_STREAMING_AUDIO': "Hey there! Let's get your music playing smoothly. Could you try logging out, restarting your device, and logging back in? You can also check your offline storage settings here: https://support.spotify.com /SC",
            'APP_CRASH_BUG': "Hi! Sorry to hear the app is giving you trouble. A clean reinstall often clears this right up. Here's a step-by-step guide: https://support.spotify.com/reinstall. Let us know if that helps! /SC",
            'PLAYLIST_LIBRARY_CATALOG': "Hey! We'd love to help with your playlist. If songs are greyed out, you can check 'Show unplayable songs' in Settings, or visit: https://support.spotify.com /SC",
            'STUDENT_DISCOUNT_HULU': "Hi there! For student plan renewals or Hulu activation, you can re-verify your student status through SheerID here: https://spotify.com/student. Give us a shout if you need a hand! /SC",
            'FAMILY_PLAN_SETUP': "Hey! To join a Family plan, make sure all members enter the exact same physical home address as the plan manager. More info: https://spotify.com/family /SC",
            'DEVICE_INTEGRATION_CONNECT': "Hey! To connect your device, ensure both devices are on the same WiFi network, then tap the Devices Available icon on the Now Playing screen. Guide: https://support.spotify.com/connect /SC",
            'DEFAULT': "Hey there! We'd love to help out. You can find detailed steps and troubleshooting guides for this here: https://support.spotify.com. Let us know how it goes! /SC"
        },
        'REQUEST_INFO_AND_REDIRECT_DM': {
            'DEFAULT': "Hi there! We'd like to look into this with you. Could you send us a DM with your account's registered email address and your device details so we can assist privately? https://twitter.com/messages/compose?recipient_id=SpotifyCares /SC"
        },
        'REQUEST_INFORMATION': {
            'OFFLINE_SYNC_DOWNLOADS': "Hey there! Could you let us know your exact iPhone model and Spotify version? Also, does this happen over WiFi or mobile data? /SC",
            'DEFAULT': "Hey! We're here to help. Could you let us know what device, operating system, and Spotify version you're currently using? /SC"
        },
        'REDIRECT_DM': {
            'DEFAULT': "Hey there! Please send us a quick DM with your account details and we'll take a look backstage for you: https://twitter.com/messages/compose?recipient_id=SpotifyCares /SC"
        },
        'TROUBLESHOOT_REINSTALL': {
            'DEFAULT': "Hey! That doesn't sound right. Could you try doing a clean reinstall of the app? Steps are here: https://support.spotify.com/reinstall. Keep us posted! /SC"
        },
        'TROUBLESHOOT_RESTART': {
            'DEFAULT': "Hi there! Can you try power cycling your device and router, then launching Spotify again? Let us know if the issue persists /SC"
        },
        'TROUBLESHOOT_UPDATE': {
            'DEFAULT': "Hey! Could you make sure your Spotify app is updated to the latest version available in your app store? /SC"
        },
        'EXPLAIN_POLICY_OR_CATALOG': {
            'DEFAULT': "Hey there! Music availability can vary depending on licensing agreements with rights holders and distributors. More info on catalog availability: https://support.spotify.com /SC"
        },
        'CONFIRM_RESOLUTION': {
            'DEFAULT': "That's awesome to hear! We're glad everything is working properly now. If you ever need anything else, just give us a shout 😊 /SC"
        },
        'CLOSING_COURTESY': {
            'DEFAULT': "You're very welcome! If there's anything else we can help with, we're just a tweet away 😉 /SC"
        },
        'ESCALATE_INTERNAL': {
            'DEFAULT': "Thanks for the details! We're passing this along to our specialized engineering team to investigate backstage. We'll update you as soon as we have news /SC"
        },
        'PROVIDE_GENERAL_ASSISTANCE': {
            'DEFAULT': "Hey! Thanks for reaching out. We'd love to help sort this out. Let us know a bit more about what's happening and we'll see what we can do /SC"
        }
    }

    LOG_PATH = "artifacts/generation_logs.jsonl"

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Guardrail 1: Pre-call Sanitization.
        Strips usernames/handles, internal IDs, and personal name greetings.
        """
        if not text:
            return ""
        # Remove user handles like @12345 or @username
        cleaned = re.sub(r'@\w+\s*', '', text).strip()
        # Remove personalized historical names like "Hey Joshua! " or "Hi David, "
        cleaned = re.sub(r'^(Hey|Hi|Hello)\s+[A-Z][a-z]+[,!]?\s*', 'Hey there! ', cleaned)
        # Remove raw trailing agent codes like /TF, /KM, /JM
        cleaned = re.sub(r'\s*/[A-Z]{2}$', '', cleaned).strip()
        return cleaned

    @classmethod
    def get_evidence_snippets(cls, matched_pathway: Optional[Dict[str, Any]], intent: str, action: str) -> List[str]:
        snippets = []
        if matched_pathway and matched_pathway.get('sample_agent_responses'):
            for r in matched_pathway['sample_agent_responses'][:3]:
                sanitized = cls.sanitize_text(r)
                if sanitized and sanitized not in snippets:
                    snippets.append(sanitized)
        
        # Fallback to curated template if evidence is empty
        if not snippets:
            action_group = cls.ACTION_TEMPLATES.get(action, cls.ACTION_TEMPLATES['PROVIDE_GENERAL_ASSISTANCE'])
            template = action_group.get(intent, action_group.get('DEFAULT', ''))
            if template:
                snippets.append(cls.sanitize_text(template))
        
        return snippets

    @classmethod
    def format_reply(cls, raw_reply: str) -> str:
        """
        Enforces 280-character Twitter length and SpotifyCares signature.
        """
        cleaned = cls.sanitize_text(raw_reply)
        if not cleaned.endswith('/SC'):
            cleaned = f"{cleaned} /SC"
        if len(cleaned) > 280:
            cleaned = cleaned[:276] + " /SC"
        return cleaned

    @classmethod
    def log_generation(cls, log_entry: Dict[str, Any]):
        """
        Guardrail 4: Log every prompt + response to an artifact file for full auditability.
        """
        try:
            os.makedirs(os.path.dirname(cls.LOG_PATH), exist_ok=True)
            with open(cls.LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
        except Exception:
            pass

    @classmethod
    def _log_generation_failure(cls, error_msg: str):
        try:
            os.makedirs(os.path.dirname(cls.LOG_PATH), exist_ok=True)
            with open(cls.LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps({
                    'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    'event': 'API_FAILURE_FALLBACK',
                    'error': error_msg
                }) + '\n')
        except Exception:
            pass

    @classmethod
    def _deterministic_template_fallback(cls, matched_pathway: Optional[Dict[str, Any]], intent: str, action: str) -> str:
        snippets = cls.get_evidence_snippets(matched_pathway, intent, action)
        if snippets:
            return snippets[0]
        action_group = cls.ACTION_TEMPLATES.get(action, cls.ACTION_TEMPLATES['PROVIDE_GENERAL_ASSISTANCE'])
        return action_group.get(intent, action_group.get('DEFAULT', 'Hey! Send us a DM and we will help: https://twitter.com/messages/compose?recipient_id=SpotifyCares /SC'))

    @classmethod
    def generate(
        cls,
        intent: str,
        state: CustomerState,
        action: str,
        matched_pathway: Optional[Dict[str, Any]] = None,
        customer_text: str = "",
        decision: str = "AUTO-HANDLE",
        return_full_result: bool = False
    ) -> Any:
        """
        Generates a grounded support reply subject to all guardrails:
          - Pre-call sanitization
          - Live Groq API execution (temp=0.2)
          - Post-generation LLM-judge verification
          - Fallback escalation on low groundedness/safety
          - Complete artifact logging
          - AUTO-HANDLE only routing
        """
        # Handle flexible argument positioning for backward compatibility
        if isinstance(matched_pathway, str) and not customer_text:
            customer_text = matched_pathway
            matched_pathway = None
        elif isinstance(customer_text, dict) and matched_pathway is None:
            matched_pathway = customer_text
            customer_text = ""

        start_time = time.time()

        # Guardrail 5: Only generate customer-facing replies for AUTO-HANDLE
        if decision != "AUTO-HANDLE":
            log_entry = {
                'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                'decision': decision,
                'intent': intent,
                'action': action,
                'customer_text': customer_text if isinstance(customer_text, str) else "",
                'status': 'SKIPPED_FOR_NON_AUTO_HANDLE',
                'reply': None
            }
            cls.log_generation(log_entry)
            if return_full_result:
                return {
                    'reply': None,
                    'status': 'SKIPPED_FOR_NON_AUTO_HANDLE',
                    'judge_scores': None,
                    'fallback_escalate': False
                }
            return f"[{decision}: Case routed to human specialist / queue — no autonomous customer reply issued]"

        # Guardrail 1: Pre-call Sanitization
        sanitized_customer_text = cls.sanitize_text(customer_text) if (customer_text and isinstance(customer_text, str)) else "Customer support inquiry."
        evidence_snippets = cls.get_evidence_snippets(matched_pathway, intent, action)
        formatted_evidence = "\n".join([f"- {s}" for s in evidence_snippets])

        prompt = cls.PROMPT_TEMPLATE.format(
            customer_text=sanitized_customer_text,
            intent=intent,
            action=action,
            evidence_snippets=formatted_evidence
        )

        # Call Groq API with low temperature (Guardrail 3)
        result = call_groq(prompt, temperature=0.2)

        if result["success"]:
            raw_reply = result["text"]
            generation_source = f"groq_{result.get('model', GROQ_MODEL)}"
            latency_ms = result["latency_ms"]
        else:
            # Fall back to deterministic template path
            raw_reply = cls._deterministic_template_fallback(matched_pathway, intent, action)
            generation_source = "deterministic_fallback"
            latency_ms = None
            cls._log_generation_failure(result["error"])

        formatted_reply = cls.format_reply(raw_reply)

        # Guardrail 2: Post-generation LLM-Judge Check
        state_dict = state.to_dict() if isinstance(state, CustomerState) else state
        judge_scores = LLMJudge.evaluate_response(
            customer_message=sanitized_customer_text,
            intent=intent,
            state=state_dict,
            action=action,
            generated_reply=formatted_reply,
            matched_pathway=matched_pathway
        )

        # Check for ungrounded promises, refunds, or safety violations
        has_hallucinated_refund = bool(re.search(r'\b(refund|credit card|guarantee|within \d+ hours)\b', formatted_reply.lower()))
        is_grounded = judge_scores['groundedness'] >= 3.5 and judge_scores['safety'] >= 4.0 and not has_hallucinated_refund

        fallback_escalate = False
        final_reply = formatted_reply

        if not is_grounded:
            # Fall back to human escalation rather than sending ungrounded/unsafe text
            fallback_escalate = True
            final_reply = "Hi there! We'd like to look into this with you privately. Please send us a DM with your account details: https://twitter.com/messages/compose?recipient_id=SpotifyCares /SC"

        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        # Guardrail 4: Log prompt + response to artifact file
        log_entry = {
            'timestamp': time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            'decision': decision,
            'intent': intent,
            'action': action,
            'customer_text': sanitized_customer_text,
            'evidence_snippets': evidence_snippets,
            'prompt': prompt,
            'raw_reply': raw_reply,
            'final_reply': final_reply,
            'generation_source': generation_source,
            'api_latency_ms': latency_ms,
            'judge_scores': judge_scores,
            'is_grounded': is_grounded,
            'fallback_escalate': fallback_escalate,
            'total_latency_ms': total_latency_ms
        }
        cls.log_generation(log_entry)

        if return_full_result:
            return {
                'reply': final_reply,
                'status': 'SUCCESS' if not fallback_escalate else 'FALLBACK_ESCALATED',
                'generation_source': generation_source,
                'judge_scores': judge_scores,
                'fallback_escalate': fallback_escalate,
                'prompt': prompt,
                'latency_ms': total_latency_ms
            }
        return final_reply

