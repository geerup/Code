"use client";

import { useState } from "react";
import { type Citation, streamChat } from "@/lib/api";

export default function Chat() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [citations, setCitations] = useState<Citation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function ask() {
    setError(null);
    setAnswer("");
    setCitations([]);
    setBusy(true);
    try {
      await streamChat(
        question,
        (c) => setCitations(c),
        (t) => setAnswer((prev) => prev + t),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Chat failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>2. Ask a question</h2>
      <input
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && !busy && question.trim() && ask()}
        placeholder="What would you like to know?"
      />
      <button onClick={ask} disabled={busy || !question.trim()}>
        {busy ? "Thinking…" : "Ask"}
      </button>

      {answer && <div className="answer">{answer}</div>}
      {error && <p className="status error">{error}</p>}

      {citations.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <label>Sources</label>
          {citations.map((c) => (
            <div className="citation" key={c.index}>
              <div className="meta">
                [{c.index}] {c.source} · score {c.score}
              </div>
              <div>{c.snippet}…</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
