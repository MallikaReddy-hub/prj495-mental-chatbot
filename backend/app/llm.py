"""Reply generation. English goes to the fine-tuned model server (with reply checks and one retry);
other languages, rejected replies and any failure go to Gemini. Medication questions get a fixed
reply. If everything fails, a gentle fallback message is returned."""
import logging
import os
import re
from collections import Counter

import httpx

log = logging.getLogger("llm")
REJECTIONS = Counter()  # use these counts in your report

MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "").rstrip("/")
LOCAL_LANGS = {"en"}  # the fine-tuned model serves English only; everything else goes to Gemini
MAX_WORDS = 80

SYSTEM = ("You are a supportive, multilingual mental health assistant. Reply in the same language as the "
          "user. Do not diagnose or prescribe. Do not recommend or discourage medication; suggest "
          "speaking to a doctor. Keep replies under 80 words. Offer one practical coping suggestion, "
          "then ask at most one gentle question.")
FALLBACK = "I'm having trouble replying right now. Please try again in a moment. I'm still here."
MEDICATION_REPLY = ("I'm not able to advise on medicines. A doctor or psychiatrist can look at your "
                    "situation and tell you what is right for you. In the meantime, slow breathing "
                    "can help a little: breathe in for 4, out for 6, a few times. What has been "
                    "worrying you the most?")

# a medicine word together with a question/decision word, e.g. "should I take medicine for anxiety"
MED_WORD = re.compile(r"\b(medicine|medicines|medication|medications|tablet|tablets|pill|pills|"
                      r"antidepressant\w*|dose|dosage|prescri\w*|drug|drugs)\b", re.I)
ASK_WORD = re.compile(r"\b(should|can|could|shall|take|taking|start|stop|which|what|how much|need|"
                      r"safe|better|recommend\w*)\b|\?", re.I)

BAD_PATTERNS = {
    "url": re.compile(r"https?://|www\.|\.com\b|\.org\b", re.I),
    "medication": re.compile(
        r"you should (take|start|stop)|\b(take|taking) \d|\d\s?mg\b|stop taking|your dose|prescribed dose|"
        r"\b(sertraline|fluoxetine|escitalopram|alprazolam|xanax|prozac|zoloft|clonazepam|diazepam|"
        r"valium|ssri|benzodiazepines?)\b|therapist near", re.I),
    "diagnosis": re.compile(
        r"\b(you have|you are|you're|you suffer from|sounds like you have)\s+"
        r"(clinical\s+)?(depress\w*|anxiety disorder|bipolar|ptsd|adhd|ocd)\b", re.I),
}


def _non_latin(text: str) -> bool:
    """True if the message contains Hindi/Kannada/other non-Latin script letters."""
    return any(ch.isalpha() and ord(ch) > 0x24F for ch in text)


def _check(reply: str) -> str | None:
    """Returns the rejection reason, or None if the reply is acceptable."""
    if not reply.strip():
        return "empty"
    if len(reply.split()) > MAX_WORDS:
        return "too_long"
    for name, pat in BAD_PATTERNS.items():
        if pat.search(reply):
            return name
    return None


def _model_server(message: str, history: list[dict]) -> str:
    r = httpx.post(f"{MODEL_SERVER_URL}/chat", json={"message": message, "history": history}, timeout=90)
    r.raise_for_status()
    return r.json()["reply"]


def _gemini(message: str, history: list[dict]) -> str:
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                for m in history]
    contents.append({"role": "user", "parts": [{"text": message}]})
    resp = client.models.generate_content(
        model=os.environ["GEMINI_MODEL"], contents=contents, config={"system_instruction": SYSTEM})
    return resp.text.strip()


def generate(message: str, history: list[dict], lang: str) -> tuple[str, str]:
    """Returns (reply, source): 'rule', 'model_server', 'gemini' or 'fallback'."""
    if lang == "en" and MED_WORD.search(message) and ASK_WORD.search(message):
        return MEDICATION_REPLY, "rule"
    if lang in LOCAL_LANGS and not _non_latin(message) and MODEL_SERVER_URL:
        for _ in range(2):  # one try plus one retry
            try:
                reply = _model_server(message, history)
            except Exception:
                break
            reason = _check(reply)
            if reason is None:
                return reply, "model_server"
            REJECTIONS[reason] += 1
            log.warning("model reply rejected: %s", reason)
    if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL"):
        try:
            return _gemini(message, history), "gemini"
        except Exception:
            pass
    return FALLBACK, "fallback"
