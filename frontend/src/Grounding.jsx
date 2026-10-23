import { useState } from "react";

const STEPS = [
  { n: 5, sense: "see", icon: "👀", prompt: "Look around and name 5 things you can see." },
  { n: 4, sense: "touch", icon: "✋", prompt: "Notice 4 things you can feel or touch: your clothes, the chair, the floor." },
  { n: 3, sense: "hear", icon: "👂", prompt: "Listen for 3 sounds, near or far." },
  { n: 2, sense: "smell", icon: "👃", prompt: "Notice 2 things you can smell, or two smells you like." },
  { n: 1, sense: "taste", icon: "👅", prompt: "Name 1 thing you can taste, or take a slow sip of water." },
];

export default function Grounding() {
  const [step, setStep] = useState(0);
  const [taps, setTaps] = useState(0);
  const finished = step >= STEPS.length;
  const s = STEPS[Math.min(step, STEPS.length - 1)];

  function tap() {
    if (taps + 1 >= s.n) { setStep(step + 1); setTaps(0); } else setTaps(taps + 1);
  }
  function restart() { setStep(0); setTaps(0); }

  return (
    <div className="ground">
      <h2>5-4-3-2-1 grounding</h2>
      <p>A way to come back to the present when your thoughts are racing. Take your time and tap each time you notice one.</p>
      {finished ? (
        <div className="ground-done">
          <div className="ground-icon">🌿</div>
          <strong>Well done.</strong>
          <p>Take one slow breath. Notice how your body feels now compared with when you started.</p>
          <button className="primary" onClick={restart}>Do it again</button>
        </div>
      ) : (
        <>
          <div className="ground-steps" aria-label={`Step ${step + 1} of 5`}>
            {STEPS.map((x, i) => <span key={x.n} className={i < step ? "dot done" : i === step ? "dot on" : "dot"}>{x.n}</span>)}
          </div>
          <div className="ground-card">
            <div className="ground-icon">{s.icon}</div>
            <strong>{s.n} things you can {s.sense}</strong>
            <p>{s.prompt}</p>
            <div className="ground-taps">
              {Array.from({ length: s.n }, (_, i) => <span key={i} className={i < taps ? "tap on" : "tap"} />)}
            </div>
            <button className="primary" onClick={tap}>I noticed one ({taps}/{s.n})</button>
          </div>
          {step > 0 || taps > 0 ? <button className="link" onClick={restart}>Start over</button> : null}
        </>
      )}
      <p className="tiny">If you feel unsafe or overwhelmed, use the Get help now button.</p>
    </div>
  );
}
