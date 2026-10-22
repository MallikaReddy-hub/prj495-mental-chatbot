import "./journal.css";
import { useEffect, useState } from "react";
import { api } from "./api";

const MOODS = [["1", "😞", "Very low"], ["2", "😕", "Low"], ["3", "😐", "Okay"], ["4", "🙂", "Good"], ["5", "😄", "Great"]];

export default function Journal() {
  const [rows, setRows] = useState([]);
  const [mood, setMood] = useState(3);
  const [note, setNote] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () => api.journal().then(setRows).catch((e) => setError(e.message));
  useEffect(() => { load(); }, []);

  async function save(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await api.saveMood({ mood, note });
      setNote(""); setMsg("Saved for today."); load();
    } catch (err) { setError(err.message); }
  }

  async function remove(id) {
    if (!confirm("Delete this entry?")) return;
    try { await api.deleteMood(id); load(); } catch (err) { setError(err.message); }
  }

  const recent = rows.slice(-14);
  return (
    <div className="journal">
      <h2>Mood journal</h2>
      <form onSubmit={save} className="j-form">
        <p>How are you today?</p>
        <div className="mood-row">
          {MOODS.map(([v, emoji, label]) => (
            <button type="button" key={v} className={mood === +v ? "mood on" : "mood"} onClick={() => setMood(+v)} aria-label={label}>
              <span>{emoji}</span><small>{label}</small>
            </button>
          ))}
        </div>
        <label>Note (optional)<textarea rows={2} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} placeholder="What affected your mood today?" /></label>
        <button className="primary">Save today's mood</button>
        {msg && <p className="tiny">{msg}</p>}
        {error && <div className="error">{error}</div>}
      </form>

      <h3>Your last {recent.length} entries</h3>
      {recent.length === 0 && <p className="tiny">No entries yet. Your chart will appear here.</p>}
      <div className="bars" role="img" aria-label="Mood chart">
        {recent.map((r) => (
          <div key={r.id} className="bar-col" title={`${r.day}: ${r.mood}/5`}>
            <div className="bar" style={{ height: `${r.mood * 20}%` }} />
            <small>{r.day.slice(5)}</small>
          </div>
        ))}
      </div>

      <ul className="j-list">
        {[...rows].reverse().map((r) => (
          <li key={r.id}>
            <span>{r.day} · {MOODS[r.mood - 1][1]} {MOODS[r.mood - 1][2]}{r.note ? ` · ${r.note}` : ""}</span>
            <button className="link" onClick={() => remove(r.id)}>Delete</button>
          </li>
        ))}
      </ul>
      <p className="tiny">This journal is for your own reflection. It is not a medical record or a diagnosis.</p>
    </div>
  );
}
