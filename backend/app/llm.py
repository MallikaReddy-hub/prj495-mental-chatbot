"""Reply generation. English/Spanish go to the fine-tuned model server; other languages (and any
failure) go to Gemini. If both fail, a gentle fallback message is returned."""
import os

import httpx

MODEL_SERVER_URL = os.getenv("MODEL_SERVER_URL", "").rstrip("/")
LOCAL_LANGS = {"en", "es"}
SYSTEM = ("You are a supportive, multilingual mental health assistant. Reply in the same language as the "
          "user. Do not diagnose or prescribe. Offer one practical coping suggestion, then ask at most "
          "one gentle question.")
FALLBACK = "I'm having trouble replying right now. Please try again in a moment. I'm still here."


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
    """Returns (reply, source) where source is 'model_server', 'gemini' or 'fallback'."""
    if lang in LOCAL_LANGS and MODEL_SERVER_URL:
        try:
            return _model_server(message, history), "model_server"
        except Exception:
            pass
    if os.getenv("GEMINI_API_KEY") and os.getenv("GEMINI_MODEL"):
        try:
            return _gemini(message, history), "gemini"
        except Exception:
            pass
    return FALLBACK, "fallback"
