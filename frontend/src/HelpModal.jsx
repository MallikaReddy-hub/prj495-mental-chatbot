import "./help.css";
import { useEffect, useState } from "react";
import { api } from "./api";

export default function HelpModal({ lang, onClose }) {
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.helplines(lang).then(setItems).catch((e) => setError(e.message));
  }, [lang]);

  return (
    <div className="overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-label="Helplines">
        <h2>You are not alone</h2>
        <p>If you are in distress, please talk to a real person. These helplines are free to call (verify the numbers before relying on them).</p>
        {error && <div className="error">{error}</div>}
        {!items && !error && <p>Loading...</p>}
        <ul className="help-list">
          {items?.map((h) => (
            <li key={h.number}>
              <span>{h.name}</span>
              <a href={`tel:${h.number.replace(/[^0-9+]/g, "")}`}>{h.number}</a>
            </li>
          ))}
        </ul>
        <p className="tiny">If you are in immediate danger, go to the nearest hospital or call your local emergency number.</p>
        <button className="primary" onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
