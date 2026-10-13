import "./auth.css";
import { useState } from "react";
import { api, setToken } from "./api";

export default function Auth({ onDone }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const r = mode === "login"
        ? await api.login({ email: form.email, password: form.password })
        : await api.signup(form);
      setToken(r.token);
      onDone();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-wrap">
      <form className="auth-card" onSubmit={submit}>
        <h1>Mindful Companion</h1>
        <p className="sub">A calm place to talk, in your own language.</p>
        {mode === "signup" && (
          <label>Name<input value={form.name} onChange={set("name")} autoComplete="name" /></label>
        )}
        <label>Email<input type="email" required value={form.email} onChange={set("email")} autoComplete="email" /></label>
        <label>Password<input type="password" required minLength={8} value={form.password} onChange={set("password")}
          autoComplete={mode === "login" ? "current-password" : "new-password"} /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy}>{busy ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}</button>
        <button type="button" className="link" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}>
          {mode === "login" ? "New here? Create an account" : "Already have an account? Log in"}
        </button>
        <p className="tiny">This app is not a substitute for professional help. If you are in crisis, call a helpline or your local emergency number.</p>
      </form>
    </div>
  );
}
