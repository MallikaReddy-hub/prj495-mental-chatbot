import "./programs.css";
import { useEffect, useState } from "react";
import { api } from "./api";

export default function Programs({ onGo }) {
  const [programs, setPrograms] = useState([]);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState("");
  const [cheer, setCheer] = useState("");

  const load = () => api.programs().then((p) => { setPrograms(p); setOpen((o) => o ?? (p.find((x) => x.done.length < x.days.length)?.id ?? p[0]?.id)); })
    .catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function toggle(p, day, done) {
    setCheer("");
    try {
      await (done ? api.undoDay(p.id, day) : api.completeDay(p.id, day));
      if (!done) setCheer(p.done.length + 1 === p.days.length ? `🎉 You finished "${p.title}". Well done!` : "Nice work. Small steps count.");
      load();
    } catch (err) { setError(err.message); }
  }

  const active = programs.filter((p) => p.done.length > 0 && p.done.length < p.days.length).length;
  const finished = programs.filter((p) => p.done.length === p.days.length).length;
  const daysDone = programs.reduce((n, p) => n + p.done.length, 0);

  return (
    <div className="programs">
      <h2>Guided programs</h2>
      <p className="tiny">Small daily steps for everyday stress. These are general self-care ideas, not treatment.</p>
      <div className="p-stats">
        <div><strong>{daysDone}</strong><small>days done</small></div>
        <div><strong>{active}</strong><small>in progress</small></div>
        <div><strong>{finished}</strong><small>finished</small></div>
      </div>
      {cheer && <div className="cheer" role="status">{cheer}</div>}
      {error && <div className="error">{error}</div>}
      {programs.map((p) => {
        const pct = Math.round((p.done.length / p.days.length) * 100);
        const next = p.days.find((d) => !p.done.includes(d.day));
        const mins = p.days.reduce((n, d) => n + (d.minutes || 0), 0);
        return (
          <details key={p.id} className="prog" open={open === p.id} onToggle={(e) => { if (e.target.open) setOpen(p.id); else if (open === p.id) setOpen(null); }}>
            <summary>
              <span className="p-emoji">{p.emoji}</span>
              <span className="p-head">
                <strong>{p.title}</strong>
                <small>{p.level} · {p.days.length} days · about {mins} min in total</small>
              </span>
              <span className={pct === 100 ? "p-pct done" : "p-pct"}>{pct === 100 ? "✓ Done" : `${pct}%`}</span>
            </summary>
            <p>{p.description}</p>
            <div className="meter" aria-label={`${pct}% complete`}><div style={{ width: `${pct}%` }} /></div>
            <ul>
              {p.days.map((d) => {
                const done = p.done.includes(d.day);
                const isNext = next?.day === d.day;
                return (
                  <li key={d.day} className={`${done ? "done" : ""} ${isNext ? "next" : ""}`}>
                    <label className="check">
                      <input type="checkbox" checked={done} onChange={() => toggle(p, d.day, done)} />
                      <span>
                        <strong>Day {d.day}: {d.title}</strong>
                        {isNext && <em className="badge">Next up</em>}
                        <small className="mins"> · {d.minutes} min</small><br />{d.task}
                      </span>
                    </label>
                    {/Breathe page/.test(d.task) && !done && <button type="button" className="link go" onClick={() => onGo?.("breathe")}>Open Breathe</button>}
                  </li>
                );
              })}
            </ul>
          </details>
        );
      })}
    </div>
  );
}
