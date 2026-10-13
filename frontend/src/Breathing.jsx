import "./breathing.css";
import { useEffect, useState } from "react";

const PHASES = [
  { label: "Breathe in", secs: 4, scale: 1.45 },
  { label: "Hold", secs: 4, scale: 1.45 },
  { label: "Breathe out", secs: 6, scale: 1 },
];

export default function Breathing() {
  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState(0);
  const [left, setLeft] = useState(PHASES[0].secs);
  const [cycles, setCycles] = useState(0);

  useEffect(() => {
    if (!running) return;
    const t = setTimeout(() => {
      if (left > 1) return setLeft(left - 1);
      const next = (phase + 1) % PHASES.length;
      if (next === 0) setCycles((c) => c + 1);
      setPhase(next);
      setLeft(PHASES[next].secs);
    }, 1000);
    return () => clearTimeout(t);
  }, [running, left, phase]);

  function toggle() {
    if (running) {
      setRunning(false);
      setPhase(0);
      setLeft(PHASES[0].secs);
    } else {
      setCycles(0);
      setRunning(true);
    }
  }

  const p = PHASES[phase];
  return (
    <div className="breathe">
      <h2>Slow breathing</h2>
      <p>Breathe in for 4, hold for 4, breathe out for 6. A few rounds can help you feel calmer.</p>
      <div className="orb-wrap">
        <div className="orb" style={{ transform: `scale(${running ? p.scale : 1})`, transitionDuration: running ? `${p.secs}s` : "0.6s" }}>
          <span>{running ? p.label : "Ready"}</span>
          {running && <small>{left}</small>}
        </div>
      </div>
      <button className="primary" onClick={toggle}>{running ? "Stop" : "Start"}</button>
      {running && <p className="tiny">Rounds completed: {cycles}</p>}
      <p className="tiny">If this makes you feel dizzy, stop and breathe normally.</p>
    </div>
  );
}
