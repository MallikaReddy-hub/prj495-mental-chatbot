"""Rule-based safety layer. Runs BEFORE the language model (crisis) and AFTER it (diagnosis guard).
The phrase lists are a minimal starting point: extend them, and have native speakers review
the Telugu, Tamil and Kannada additions."""
import re

CRISIS = re.compile(
    r"suicid|kill myself|end my life|want to die|wanna die|hurt myself|self.?harm|don'?t want to live"
    r"|आत्महत्या|मरना चाहत|जान दे|खुद को खत्म|जीना नहीं चाहत"
    r"|suicidio|quitarme la vida|quiero morir|hacerme daño|no quiero vivir", re.I)

DIAGNOSIS = re.compile(
    r"\byou (probably |likely )?(have|are suffering from) (depression|anxiety|bipolar|adhd|ptsd|ocd)"
    r"|\byou may have (depression|anxiety|bipolar|adhd|ptsd|ocd)"
    r"|it'?s possible that (what )?you('re| are) (experiencing|having|suffering)[^.]{0,40}(depression|anxiety|bipolar|adhd|ptsd|ocd)"
    r"|es posible que tengas (ansiedad|depresi[oó]n)|\btienes (ansiedad|depresi[oó]n)"
    r"|आपको (डिप्रेशन|अवसाद|एंग्जायटी|चिंता विकार) (है|हो सकता)", re.I)

CRISIS_TEXT = {
    "en": "I'm really sorry you're in so much pain. You deserve support from a real person right now. "
          "Please reach out to someone you trust, or call one of these helplines:",
    "hi": "मुझे सचमुच दुख है कि आप इतने दर्द में हैं। इस समय आपको किसी असली व्यक्ति का साथ मिलना चाहिए। "
          "कृपया किसी भरोसेमंद व्यक्ति से बात करें, या इन हेल्पलाइन पर कॉल करें:",
    "es": "Lamento mucho que estés sufriendo tanto. Mereces apoyo de una persona real ahora mismo. "
          "Por favor, habla con alguien de confianza o llama a una de estas líneas de ayuda:",
}
CRISIS_END = {
    "en": "If you are in immediate danger, go to the nearest hospital or call your local emergency number.",
    "hi": "यदि आप तुरंत खतरे में हैं, तो नज़दीकी अस्पताल जाएँ या अपने स्थानीय आपातकालीन नंबर पर कॉल करें।",
    "es": "Si estás en peligro inmediato, acude al hospital más cercano o llama a tu número de emergencias.",
}
SAFE_FALLBACK = {
    "en": "I can't diagnose anything, but I'm here to listen. A doctor or counselor can look at this properly. "
          "Would you like to tell me more about what you've been feeling?",
    "hi": "मैं कोई निदान नहीं कर सकता, लेकिन मैं सुनने के लिए यहाँ हूँ। डॉक्टर या काउंसलर इसे सही तरह से देख सकते हैं। "
          "क्या आप बताना चाहेंगे कि आप कैसा महसूस कर रहे हैं?",
    "es": "No puedo diagnosticar nada, pero estoy aquí para escucharte. Un médico o consejero puede evaluarlo bien. "
          "¿Quieres contarme más sobre lo que sientes?",
}


def is_crisis(text: str) -> bool:
    return bool(CRISIS.search(text))


def crisis_message(lang: str, helplines: list[dict]) -> str:
    # te/ta/kn fall back to English until native-speaker-reviewed text is added
    key = lang if lang in CRISIS_TEXT else "en"
    lines = "\n".join(f"- {h['name']}: {h['number']}" for h in helplines)
    return f"{CRISIS_TEXT[key]}\n{lines}\n\n{CRISIS_END[key]}"


def guard(reply: str, lang: str) -> str:
    """Replace diagnosis-like replies with a safe fallback."""
    if DIAGNOSIS.search(reply):
        return SAFE_FALLBACK.get(lang, SAFE_FALLBACK["en"])
    return reply
