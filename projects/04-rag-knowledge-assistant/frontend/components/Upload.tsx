"use client";

import { useState } from "react";
import { ingestText } from "@/lib/api";

export default function Upload({ onIngested }: { onIngested: () => void }) {
  const [source, setSource] = useState("");
  const [text, setText] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    setError(null);
    setStatus(null);
    setBusy(true);
    try {
      const result = await ingestText(source || "pasted-text", text);
      setStatus(`Ingested "${result.source}" into ${result.chunks} chunk(s).`);
      setText("");
      onIngested();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ingest failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel">
      <h2>1. Add knowledge</h2>
      <label htmlFor="source">Source name</label>
      <input
        id="source"
        value={source}
        onChange={(e) => setSource(e.target.value)}
        placeholder="e.g. company-handbook.md"
      />
      <label htmlFor="text">Document text</label>
      <textarea
        id="text"
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste the text you want to ask questions about…"
      />
      <button onClick={submit} disabled={busy || !text.trim()}>
        {busy ? "Ingesting…" : "Ingest"}
      </button>
      {status && <p className="status">{status}</p>}
      {error && <p className="status error">{error}</p>}
    </div>
  );
}
