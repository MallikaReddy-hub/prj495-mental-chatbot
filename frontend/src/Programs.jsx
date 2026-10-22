import "./programs.css";
import { useEffect, useState } from "react";
import { api } from "./api";

export default function Programs() {
  const [programs, setPrograms] = useState([]);
  const [error, setError] = useState("");

  const load = () => api.programs().then(setPrograms).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function toggle(p, day, done) {
    try {
      await (done ? api.undoDay(p.id, day) : api.completeDay(p.id, day));
      load();
    } catch (err) { setError(err.message); }
  }

  return (
    <div className="programs">
      <h2>Guided programs</h2>
      <p className="tiny">Small daily steps for everyday stress. These are general self-care ideas, not treatment.</p>
      {error && <div className="error">{error}</div>}
      {programs.map((p) => {
        const pct = Math.round((p.done.length / p.days.length) * 100);
        return (
          <section key={p.id} className="prog">
            <h3>{p.title}</h3>
            <p>{p.description}</p>
            <div className="meter" aria-label={`${pct}% complete`}><div style={{ width: `${pct}%` }} /></div>
            <ul>
              {p.days.map((d) => {
                const done = p.done.includes(d.day);
                return (
                  <li key={d.day} className={done ? "done" : ""}>
                    <label className="check">
                      <input type="checkbox" checked={done} onChange={() => toggle(p, d.day, done)} />
                      <span><strong>Day {d.day}: {d.title}</strong><br />{d.task}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </section>
        );
      })}
    </div>
  );
}
