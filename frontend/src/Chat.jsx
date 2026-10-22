import "./chat.css";
import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import { useVoice } from "./useVoice.js";

export const LANGS = [
  ["en", "English"], ["hi", "हिन्दी"], ["te", "తెలుగు"],
  ["ta", "தமிழ்"], ["kn", "ಕನ್ನಡ"], ["es", "Español"],
];

export default function Chat({ lang, setLang, onHelp }) {
  const [convs, setConvs] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [quote, setQuote] = useState("");
  const [sideOpen, setSideOpen] = useState(false);
  const endRef = useRef(null);
  const voice = useVoice(lang);
  const [rated, setRated] = useState({});

  const loadConvs = () => api.conversations().then(setConvs).catch(() => {});

  useEffect(() => {
    loadConvs();
    api.quote().then((r) => setQuote(r.quote)).catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  async function openConv(id) {
    setError("");
    setSideOpen(false);
    try {
      const c = await api.conversation(id);
      setActiveId(id);
      setMessages(c.messages);
    } catch (e) {
      setError(e.message);
    }
  }

  function newChat() {
    setActiveId(null);
    setMessages([]);
    setError("");
    setSideOpen(false);
  }

  async function removeConv(id) {
    if (!confirm("Delete this conversation?")) return;
    try {
      await api.deleteConversation(id);
      if (id === activeId) newChat();
      loadConvs();
    } catch (e) {
      setError(e.message);
    }
  }

  async function send(e) {
    e?.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setError("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setBusy(true);
    try {
      const r = await api.chat({ message: text, language: lang, conversation_id: activeId });
      setMessages((m) => [...m, { id: r.message_id, role: "assistant", content: r.reply, is_crisis: r.is_crisis }]);
      if (!activeId) {
        setActiveId(r.conversation_id);
        loadConvs();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function rate(m, rating) {
    if (!m.id || rated[m.id]) return;
    try {
      await api.feedback({ message_id: m.id, rating });
      setRated((r) => ({ ...r, [m.id]: rating }));
    } catch (err) { setError(err.message); }
  }

  function toggleMic() {
    if (voice.listening) return voice.stop();
    setError("");
    voice.listen((text) => setInput((v) => (v ? v + " " : "") + text), setError);
  }

  function download() {
    const text = messages.map((m) => `${m.role === "user" ? "Me" : "Companion"}: ${m.content}`).join("\n\n");
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const a = document.createElement("a");
    a.href = url; a.download = "my-chat.txt"; a.click();
    URL.revokeObjectURL(url);
  }

  function onKey(e) {
    if (e.key === "Enter" && !e.shiftKey) send(e);
  }

  return (
    <div className="chat-layout">
      <aside className={sideOpen ? "side open" : "side"}>
        <button className="primary" onClick={newChat}>+ New chat</button>
        <div className="conv-list">
          {convs.length === 0 && <p className="tiny">Your saved chats will appear here.</p>}
          {convs.map((c) => (
            <div key={c.id} className={c.id === activeId ? "conv on" : "conv"}>
              <button className="conv-title" onClick={() => openConv(c.id)}>{c.title || "Chat"}</button>
              <button className="conv-del" aria-label="Delete chat" onClick={() => removeConv(c.id)}>×</button>
            </div>
          ))}
        </div>
      </aside>

      <section className="chat">
        <div className="chat-bar">
          <button className="hist" onClick={() => setSideOpen(!sideOpen)}>History</button>
          {messages.length > 0 && <button className="hist show" onClick={download}>Download chat</button>}
          <label className="lang">
            Language
            <select value={lang} onChange={(e) => setLang(e.target.value)}>
              {LANGS.map(([code, label]) => <option key={code} value={code}>{label}</option>)}
            </select>
          </label>
        </div>

        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <h2>How are you feeling today?</h2>
              {quote && <blockquote>Thought of the day: {quote}</blockquote>}
              <p>Type in your language and I'll reply in the same language.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}${m.is_crisis ? " crisis" : ""}`}>
              <div className="bubble">{m.content}</div>
              {m.is_crisis && <button className="link" onClick={onHelp}>Open helplines</button>}
              {m.role === "assistant" && (
                <div className="tools">
                  <button aria-label="Read aloud" onClick={() => voice.speak(m.content, setError)}>🔊</button>
                  {m.id && (
                    <>
                      <button aria-label="Helpful" className={rated[m.id] === 1 ? "on" : ""} onClick={() => rate(m, 1)}>👍</button>
                      <button aria-label="Not helpful" className={rated[m.id] === -1 ? "on" : ""} onClick={() => rate(m, -1)}>👎</button>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
          {busy && <div className="msg assistant"><div className="bubble typing">Thinking...</div></div>}
          {error && <div className="error">{error}</div>}
          <div ref={endRef} />
        </div>

        <form className="composer" onSubmit={send}>
          <textarea rows={2} value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={onKey}
            placeholder="Write how you feel..." maxLength={2000} />
          <button type="button" className={voice.listening ? "mic on" : "mic"} onClick={toggleMic}
            aria-label="Speak your message" title="Speak (uses your browser's speech service)">🎤</button>
          <button className="primary" disabled={busy || !input.trim()}>Send</button>
        </form>
      </section>
    </div>
  );
}
