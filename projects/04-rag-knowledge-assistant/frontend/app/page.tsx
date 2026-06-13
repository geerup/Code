"use client";

import { useState } from "react";
import Chat from "@/components/Chat";
import Upload from "@/components/Upload";

export default function Home() {
  // Bump to let Chat/Upload know the corpus changed (kept simple for the demo).
  const [, setVersion] = useState(0);

  return (
    <main className="container">
      <h1>RAG Knowledge Assistant</h1>
      <p className="subtitle">
        Ingest your own documents, then ask questions answered <em>only</em> from
        them — with inline citations. Powered by a local LLM via Ollama.
      </p>
      <Upload onIngested={() => setVersion((v) => v + 1)} />
      <Chat />
    </main>
  );
}
