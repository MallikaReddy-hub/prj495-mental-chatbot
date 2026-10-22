import "./plan.css";
import { useEffect, useState } from "react";
import { api } from "./api";

export default function SafetyPlan() {
  const [plan, setPlan] = useState({ contact_name: "", contact_phone: "", coping_steps: "", safe_place: "" });
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { api.plan().then(setPlan).catch((e) => setError(e.message)); }, []);
  const set = (k) => (e) => setPlan({ ...plan, [k]: e.target.value });

  async function save(e) {
    e.preventDefault();
    setMsg(""); setError("");
    try { await api.savePlan(plan); setMsg("Saved. This plan is shown to you if a message looks like a crisis."); }
    catch (err) { setError(err.message); }
  }

  return (
    <form className="plan" onSubmit={save}>
      <h2>My safety plan</h2>
      <p>Fill this in while you feel calm. If the chat ever detects a crisis, your plan appears next to the helplines.</p>
      <label>A person I can reach out to<input maxLength={100} value={plan.contact_name} onChange={set("contact_name")} /></label>
      <label>Their phone number<input maxLength={30} value={plan.contact_phone} onChange={set("contact_phone")} /></label>
      <label>Things that help me calm down<textarea rows={3} maxLength={800} value={plan.coping_steps} onChange={set("coping_steps")} placeholder="e.g. a walk, music, slow breathing" /></label>
      <label>A place where I feel safe<input maxLength={200} value={plan.safe_place} onChange={set("safe_place")} /></label>
      <button className="primary">Save my plan</button>
      {msg && <p className="tiny">{msg}</p>}
      {error && <div className="error">{error}</div>}
      <p className="tiny">Your plan is private to your account. Helplines are always available from the Get help now button.</p>
    </form>
  );
}
