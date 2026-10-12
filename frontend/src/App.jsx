import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";
import Auth from "./Auth.jsx";
import Chat from "./Chat.jsx";
import Breathing from "./Breathing.jsx";
import HelpModal from "./HelpModal.jsx";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getToken());
  const [name, setName] = useState("");
  const [tab, setTab] = useState("chat");
  const [lang, setLang] = useState("en");
  const [helpOpen, setHelpOpen] = useState(false);

  useEffect(() => {
    const expired = () => setLoggedIn(false);
    window.addEventListener("auth-expired", expired);
    return () => window.removeEventListener("auth-expired", expired);
  }, []);

  useEffect(() => {
    if (loggedIn) api.me().then((u) => setName(u.name || "")).catch(() => {});
  }, [loggedIn]);

  function logout() {
    setToken(null);
    setLoggedIn(false);
  }

  async function deleteAccount() {
    if (!confirm("Delete your account and ALL your chats? This cannot be undone.")) return;
    try {
      await api.deleteAccount();
      logout();
    } catch (e) {
      alert(e.message);
    }
  }

  if (!loggedIn) return <Auth onDone={() => setLoggedIn(true)} />;

  return (
    <div className="app">
      <header className="top">
        <div className="brand">Mindful Companion</div>
        <nav>
          <button className={tab === "chat" ? "tab on" : "tab"} onClick={() => setTab("chat")}>Chat</button>
          <button className={tab === "breathe" ? "tab on" : "tab"} onClick={() => setTab("breathe")}>Breathe</button>
        </nav>
        <div className="actions">
          <button className="help-btn" onClick={() => setHelpOpen(true)}>Get help now</button>
          <details className="menu">
            <summary>{name || "Account"}</summary>
            <div className="menu-box">
              <button onClick={logout}>Log out</button>
              <button className="danger" onClick={deleteAccount}>Delete my account</button>
            </div>
          </details>
        </div>
      </header>

      <main>
        {tab === "chat" ? <Chat lang={lang} setLang={setLang} onHelp={() => setHelpOpen(true)} /> : <Breathing />}
      </main>

      <footer className="note">
        This is an AI support companion, not a doctor or therapist. It cannot diagnose or give medical advice.
      </footer>

      {helpOpen && <HelpModal lang={lang} onClose={() => setHelpOpen(false)} />}
    </div>
  );
}
