import "./journal.css";
import { useEffect, useState } from "react";
import { api } from "./api";

const MOODS = [["1", "😞", "Very low"], ["2", "😕", "Low"], ["3", "😐", "Okay"], ["4", "🙂", "Good"], ["5", "😄", "Great"]];
const SLEEP = [4, 5, 6, 7, 8, 9];
const TAGS = ["exams", "study", "family", "friends", "health", "work", "money", "lonely", "tired", "calm", "grateful"];
const MOOD_WORD = ["", "Very low", "Low", "Okay", "Good", "Great"];

const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time

function Trend({ now, before, unit = "" }) {
  if (now == null || before == null) return <small>Not enough data yet</small>;
  const d = Math.round((now - before) * 10) / 10;
  if (d === 0) return <small>→ Same as the previous 5 check-ins</small>;
  return <small>{d > 0 ? "↑" : "↓"} {Math.abs(d)}{unit} {d > 0 ? "higher" : "lower"} than the previous 5</small>;
}

export default function Journal() {
  const [rows, setRows] = useState([]);
  const [sum, setSum] = useState(null);
  const [mood, setMood] = useState(3);
  const [sleep, setSleep] = useState(null);
  const [tags, setTags] = useState([]);
  const [note, setNote] = useState("");
  const [query, setQuery] = useState("");
  const [msg, setMsg] = useState("");
  const [error, setError] = useState("");

  const load = () => {
    api.journal().then((r) => {
      setRows(r);
      const t = r.find((x) => x.day === today());
      if (t) { setMood(t.mood); setSleep(t.sleep_hours); setTags(t.tags || []); setNote(t.note || ""); }
    }).catch((e) => setError(e.message));
    api.journalSummary().then(setSum).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const toggleTag = (t) => setTags((cur) => cur.includes(t) ? cur.filter((x) => x !== t) : cur.length < 6 ? [...cur, t] : cur);

  async function save(e) {
    e.preventDefault();
    setError(""); setMsg("");
    try {
      await api.saveMood({ mood, note, sleep_hours: sleep, tags, day: today() });
      setMsg("Saved for today. Well done for checking in."); load();
    } catch (err) { setError(err.message); }
  }

  async function remove(id) {
    if (!confirm("Delete this entry?")) return;
    try { await api.deleteMood(id); load(); } catch (err) { setError(err.message); }
  }

  const recent = rows.slice(-14);
  const q = query.trim().toLowerCase();
  const shown = [...rows].reverse().filter((r) => !q || `${r.note} ${(r.tags || []).join(" ")} ${r.day}`.toLowerCase().includes(q));
  const avgMood = sum?.last?.mood;

  return (
    <div className="journal">
      <h2>Mood journal</h2>
      <div className="cards">
        <div className="stat mood-card">
          <span className="stat-title">Average mood <small>(last {sum?.count || 0} check-ins)</small></span>
          <strong>{avgMood != null ? `${MOODS[Math.round(avgMood) - 1][1]} ${MOOD_WORD[Math.round(avgMood)]}` : "No data yet"}</strong>
          <Trend now={avgMood} before={sum?.previous?.mood} />
        </div>
        <div className="stat sleep-card">
          <span className="stat-title">Average sleep <small>(last {sum?.count || 0} check-ins)</small></span>
          <strong>{sum?.last?.sleep != null ? `😴 ${sum.last.sleep} hours` : "No data yet"}</strong>
          <Trend now={sum?.last?.sleep} before={sum?.previous?.sleep} unit="h" />
        </div>
        <div className="stat streak-card">
          <span className="stat-title">Check-in streak</span>
          <strong>🔥 {sum?.streak || 0} {sum?.streak === 1 ? "day" : "days"}</strong>
          <small>{sum?.logged_today ? "You have checked in today" : "Check in today to keep it going"}</small>
        </div>
      </div>

      <form onSubmit={save} className="j-form">
        <p><strong>How are you feeling today?</strong></p>
        <div className="mood-row">
          {MOODS.map(([v, emoji, label]) => (
            <button type="button" key={v} className={mood === +v ? `mood on m${v}` : "mood"} onClick={() => setMood(+v)} aria-label={label} aria-pressed={mood === +v}>
              <span>{emoji}</span><small>{label}</small>
            </button>
          ))}
        </div>

        <p className="field-title">How many hours did you sleep last night?</p>
        <div className="chips">
          {SLEEP.map((h) => (
            <button type="button" key={h} className={sleep === h ? "chip on" : "chip"} onClick={() => setSleep(sleep === h ? null : h)} aria-pressed={sleep === h}>
              {h === 9 ? "9+" : h === 4 ? "≤4" : h} h
            </button>
          ))}
        </div>

        <p className="field-title">What is on your mind? <small>(pick up to 6)</small></p>
        <div className="chips">
          {TAGS.map((t) => (
            <button type="button" key={t} className={tags.includes(t) ? "chip on" : "chip"} onClick={() => toggleTag(t)} aria-pressed={tags.includes(t)}>{t}</button>
          ))}
        </div>

        <label>{sum?.prompt || "What affected your mood today?"}
          <textarea rows={2} maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} placeholder="Write a line or two (optional)" />
        </label>
        <button className="primary">{sum?.logged_today ? "Update today's check-in" : "Save today's check-in"}</button>
        {msg && <p className="tiny">{msg}</p>}
        {error && <div className="error">{error}</div>}
      </form>

      <h3>Mood and sleep, last {recent.length || 14} days</h3>
      {recent.length === 0 && <p className="tiny">No entries yet. Your chart will appear here.</p>}
      <div className="bars" role="img" aria-label="Mood and sleep chart">
        {recent.map((r) => (
          <div key={r.id} className="bar-col" title={`${r.day}: mood ${r.mood}/5${r.sleep_hours != null ? `, sleep ${r.sleep_hours}h` : ""}`}>
            <span className="bar-face">{MOODS[r.mood - 1][1]}</span>
            <div className={`bar m${r.mood}`} style={{ height: `${r.mood * 13}%` }} />
            <small>{r.day.slice(5)}</small>
            <small className="bar-sleep">{r.sleep_hours != null ? `${r.sleep_hours}h` : "·"}</small>
          </div>
        ))}
      </div>

      <div className="j-head">
        <h3>Your entries</h3>
        <input type="search" className="j-search" placeholder="Search notes or tags" value={query} onChange={(e) => setQuery(e.target.value)} aria-label="Search entries" />
      </div>
      {shown.length === 0 && <p className="tiny">{rows.length ? "Nothing matches your search." : "Nothing here yet."}</p>}
      <ul className="j-list">
        {shown.map((r) => (
          <li key={r.id}>
            <span>
              <strong>{r.day}</strong> · {MOODS[r.mood - 1][1]} {MOODS[r.mood - 1][2]}
              {r.sleep_hours != null ? ` · 😴 ${r.sleep_hours}h` : ""}
              {(r.tags || []).map((t) => <em key={t} className="tag">{t}</em>)}
              {r.note ? <><br />{r.note}</> : null}
            </span>
            <button className="link" onClick={() => remove(r.id)}>Delete</button>
          </li>
        ))}
      </ul>
      <p className="tiny">This journal is for your own reflection. It is not a medical record or a diagnosis.</p>
    </div>
  );
}
