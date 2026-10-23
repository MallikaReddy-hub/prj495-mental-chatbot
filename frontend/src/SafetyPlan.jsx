import "./plan.css";
import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const EMPTY = { contact_name: "", contact_phone: "", contact2_name: "", contact2_phone: "", coping_steps: "",
  safe_place: "", warning_signs: "", reasons: "", make_safe: "" };

const SECTIONS = [
  { id: "warning", icon: "🚦", title: "My warning signs", hint: "Thoughts, feelings or situations that tell me things are getting harder.", keys: ["warning_signs"] },
  { id: "coping", icon: "🌿", title: "Things that help me calm down", hint: "Things I can do on my own: a walk, music, slow breathing, a shower.", keys: ["coping_steps"] },
  { id: "people", icon: "📞", title: "People I can reach out to", hint: "Someone I trust who I can call or message.", keys: ["contact_name", "contact_phone", "contact2_name", "contact2_phone"] },
  { id: "place", icon: "🏡", title: "A place where I feel safe", hint: "A room, a park, a friend's home.", keys: ["safe_place"] },
  { id: "safer", icon: "🛡️", title: "Making my space safer", hint: "One step to keep anything that could hurt me out of reach, or to ask someone to hold it for me.", keys: ["make_safe"] },
  { id: "reasons", icon: "💛", title: "My reasons to keep going", hint: "People, goals or small things that matter to me.", keys: ["reasons"] },
];

const REMEMBER = [
  "I am resilient and capable of getting through hard moments.",
  "My worth is not determined by my struggles.",
  "I have the strength to get through difficult moments, one at a time.",
  "I can focus on the present moment, and this feeling will change.",
  "My feelings are valid, and it is okay to ask for help when I need it.",
];

const digits = (p) => p.replace(/[^\d+]/g, "");

export default function SafetyPlan({ onHelp }) {
  const [plan, setPlan] = useState(EMPTY);
  const [saved, setSaved] = useState(EMPTY);
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");
  const [r, setR] = useState(0);
  const [preview, setPreview] = useState(false);

  useEffect(() => { api.plan().then((p) => { setPlan({ ...EMPTY, ...p }); setSaved({ ...EMPTY, ...p }); }).catch((e) => setError(e.message)); }, []);
  const set = (k) => (e) => setPlan({ ...plan, [k]: e.target.value });
  const filled = SECTIONS.filter((s) => s.keys.some((k) => plan[k].trim())).length;
  const pct = Math.round((filled / SECTIONS.length) * 100);
  const dirty = JSON.stringify(plan) !== JSON.stringify(saved);

  const previewLines = useMemo(() => {
    const L = [];
    [[plan.contact_name, plan.contact_phone], [plan.contact2_name, plan.contact2_phone]].forEach(([n, p]) => { if (n || p) L.push(`Reach out to: ${n} ${p}`.trim()); });
    if (plan.coping_steps) L.push(`Things that help you: ${plan.coping_steps}`);
    if (plan.safe_place) L.push(`A safe place for you: ${plan.safe_place}`);
    if (plan.make_safe) L.push(`Making your space safer: ${plan.make_safe}`);
    if (plan.reasons) L.push(`Your reasons to keep going: ${plan.reasons}`);
    return L;
  }, [plan]);

  async function save(e) {
    e.preventDefault();
    setMsg(""); setError("");
    try { await api.savePlan(plan); setSaved(plan); setMsg("Saved. This plan is shown to you if a message looks like a crisis."); }
    catch (err) { setError(err.message); }
  }

  const field = (k, label, props = {}) => (
    <label>{label}<input maxLength={k.includes("phone") ? 30 : 100} value={plan[k]} onChange={set(k)} {...props} /></label>
  );
  const area = (k, placeholder) => <textarea rows={2} maxLength={800} value={plan[k]} onChange={set(k)} placeholder={placeholder} />;

  return (
    <form className="plan" onSubmit={save}>
      <h2>My safety plan</h2>
      <p>Fill this in while you feel calm. If the chat ever detects a crisis, your plan appears next to the helplines.</p>
      <div className="plan-progress">
        <div className="meter" aria-label={`${pct}% complete`}><div style={{ width: `${pct}%` }} /></div>
        <small>{filled} of {SECTIONS.length} sections filled</small>
      </div>
      <div className="plan-actions">
        <button type="button" className="help-btn" onClick={onHelp}>Get help now</button>
      </div>

      <div className="remember">
        <strong>Just remember</strong>
        <p>“{REMEMBER[r]}”</p>
        <button type="button" className="link" onClick={() => setR((r + 1) % REMEMBER.length)}>Show another</button>
      </div>

      {SECTIONS.map((s, i) => (
        <section key={s.id} className="plan-card">
          <h3><span className="plan-n">{i + 1}</span> {s.icon} {s.title}</h3>
          <p className="tiny">{s.hint}</p>
          {s.id === "warning" && area("warning_signs", "e.g. not sleeping, pulling away from friends, feeling hopeless")}
          {s.id === "coping" && area("coping_steps", "e.g. a walk, music, slow breathing")}
          {s.id === "people" && (
            <>
              <div className="pair">{field("contact_name", "Name")}{field("contact_phone", "Phone", { inputMode: "tel" })}
                {plan.contact_phone && <a className="call" href={`tel:${digits(plan.contact_phone)}`}>📞 Call</a>}</div>
              <div className="pair">{field("contact2_name", "Second person (optional)")}{field("contact2_phone", "Phone", { inputMode: "tel" })}
                {plan.contact2_phone && <a className="call" href={`tel:${digits(plan.contact2_phone)}`}>📞 Call</a>}</div>
            </>
          )}
          {s.id === "place" && <input maxLength={200} value={plan.safe_place} onChange={set("safe_place")} placeholder="e.g. the terrace, my friend's home" aria-label="A safe place" />}
          {s.id === "safer" && area("make_safe", "e.g. ask a family member to keep medicines with them")}
          {s.id === "reasons" && area("reasons", "e.g. my family, finishing my degree, my pet")}
        </section>
      ))}

      <button className="primary" disabled={!dirty}>{dirty || !filled ? "Save my plan" : "Plan saved"}</button>
      {msg && <p className="tiny">{msg}</p>}
      {error && <div className="error">{error}</div>}

      <button type="button" className="link" onClick={() => setPreview(!preview)}>{preview ? "Hide" : "Show"} what I would see in a crisis</button>
      {preview && (
        <div className="crisis-preview">
          <strong>Your own safety plan:</strong>
          {previewLines.length ? previewLines.map((l) => <div key={l}>- {l}</div>) : <div className="tiny">Nothing filled in yet.</div>}
        </div>
      )}
      <p className="tiny">Your plan is private to your account. Helplines are always available from the Get help now button.</p>
    </form>
  );
}
