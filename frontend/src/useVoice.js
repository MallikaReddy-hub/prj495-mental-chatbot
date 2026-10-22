import { useRef, useState } from "react";

const LOCALE = { en: "en-IN", hi: "hi-IN", te: "te-IN", ta: "ta-IN", kn: "kn-IN", es: "es-ES" };

// Browser speech: input uses the browser's recognition service (Chrome/Edge); output uses installed voices.
export function useVoice(lang) {
  const SR = typeof window !== "undefined" && (window.SpeechRecognition || window.webkitSpeechRecognition);
  const [listening, setListening] = useState(false);
  const recRef = useRef(null);

  function listen(onText, onError) {
    if (!SR) return onError("Voice input isn't supported in this browser. Try Chrome or Edge.");
    const rec = new SR();
    rec.lang = LOCALE[lang] || "en-IN";
    rec.interimResults = false;
    rec.onresult = (e) => onText(e.results[0][0].transcript);
    rec.onerror = (e) => {
      setListening(false);
      onError(e.error === "not-allowed" ? "Microphone permission was blocked." : "Couldn't hear that. Please try again.");
    };
    rec.onend = () => setListening(false);
    recRef.current = rec;
    setListening(true);
    rec.start();
  }

  function stop() { recRef.current?.stop(); }

  function speak(text, onError) {
    if (!("speechSynthesis" in window)) return onError("Spoken replies aren't supported in this browser.");
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = LOCALE[lang] || "en-IN";
    const voice = window.speechSynthesis.getVoices().find((v) => v.lang === u.lang);
    if (voice) u.voice = voice;
    else if (lang !== "en" && lang !== "es") onError("No voice for this language is installed on your device, so it may not sound right.");
    window.speechSynthesis.speak(u);
  }

  return { listening, listen, stop, speak };
}
