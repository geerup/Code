// Thin client for the RAG backend. The base URL is configured at build time via
// NEXT_PUBLIC_API_URL (set this to your Fly/Render URL in Vercel).

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface Citation {
  index: number;
  source: string;
  score: number;
  snippet: string;
}

export interface IngestResult {
  document_id: number;
  chunks: number;
  source: string;
}

export async function ingestText(source: string, text: string): Promise<IngestResult> {
  const res = await fetch(`${API_URL}/ingest`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ source, text }),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Ingest failed (${res.status})`);
  }
  return res.json();
}

// Streams the answer, invoking callbacks as NDJSON frames arrive.
export async function streamChat(
  question: string,
  onCitations: (c: Citation[]) => void,
  onToken: (t: string) => void,
): Promise<void> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok || !res.body) {
    throw new Error(`Chat failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.trim()) continue;
      const frame = JSON.parse(line);
      if (frame.type === "citations") onCitations(frame.citations);
      else if (frame.type === "token") onToken(frame.value);
    }
  }
}
