// The single source of truth for the portfolio: every project, its theme,
// stack, status, and a one-line pitch. The index page renders from this, and a
// unit test guards its integrity (30 entries, unique ids, valid themes).

export const THEMES = ['AI', 'Games', 'Creative', 'Systems', 'Full-stack'];

export const PROJECTS = [
  { id: 1, slug: '01-social-app', name: 'microfeed', theme: 'Full-stack', stack: 'Go · SSE', flagship: false, status: 'built',
    blurb: 'Real-time microblog: follow graph, home feed, likes, live updates over SSE.' },
  { id: 2, slug: '02-multiplayer-arena', name: 'Coin Arena', theme: 'Games', stack: 'Go · WebSocket', flagship: false, status: 'built',
    blurb: 'Authoritative-server real-time multiplayer with a tested, transport-free sim.' },
  { id: 3, slug: '03-generative-art-playground', name: 'Generative Art Playground', theme: 'Creative', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'Seedable, shareable generative art (flow field, subdivision, circle packing).' },
  { id: 4, slug: '04-rag-knowledge-assistant', name: 'RAG Knowledge Assistant', theme: 'AI', stack: 'FastAPI · Next.js', flagship: false, status: 'shipped',
    blurb: 'Ask questions over your docs, answered only from them, with citations.' },
  { id: 5, slug: '05-agentic-task-runner', name: 'Agentic Task Runner', theme: 'AI', stack: 'Python', flagship: false, status: 'built',
    blurb: 'A compact ReAct loop: plan → call tools → observe → answer, with step caps.' },
  { id: 6, slug: '06-code-review-cli', name: 'LLM Code-Review CLI', theme: 'AI', stack: 'Go', flagship: false, status: 'built',
    blurb: 'Reviews a git diff via a local model; injectable LLM, fully tested offline.' },
  { id: 7, slug: '07-ai-games-bridge', name: 'AI + Games Bridge', theme: 'Games', stack: 'Python', flagship: false, status: 'built',
    blurb: 'English → validated, playable level JSON via a validate-then-repair pipeline.' },
  { id: 8, slug: '08-vector-search', name: 'Vector Search Engine', theme: 'Systems', stack: 'Go', flagship: false, status: 'built',
    blurb: 'From-scratch cosine + LSH ANN, with recall measured against exact search.' },
  { id: 9, slug: '09-ai-game-master', name: 'AI Game Master', theme: 'Games', stack: 'Python', flagship: true, status: 'built',
    blurb: 'Text adventure where the engine owns state and rejects hallucinated effects.' },
  { id: 10, slug: '10-ai-party-game', name: 'AI Party Game', theme: 'Games', stack: 'Python', flagship: true, status: 'built',
    blurb: 'Quiplash-style rooms with an LLM judge and an authoritative state machine.' },
  { id: 11, slug: '11-eval-harness', name: 'Prompt-Eval Harness', theme: 'AI', stack: 'Python', flagship: false, status: 'built',
    blurb: 'JSONL evals with mechanical metrics + LLM-judge and a CI regression gate.' },
  { id: 12, slug: '12-multi-agent-research', name: 'Multi-Agent Research Crew', theme: 'AI', stack: 'Python', flagship: true, status: 'built',
    blurb: 'Planner/Researcher/Writer/Critic collaborate into a cited report.' },
  { id: 13, slug: '13-chat-bot', name: 'LLM Chat-Bot', theme: 'AI', stack: 'Python', flagship: false, status: 'built',
    blurb: 'Telegram webhook bot with per-chat memory; deployable as a worker.' },
  { id: 14, slug: '14-npc-dialogue', name: 'NPC Dialogue Engine', theme: 'Games', stack: 'JavaScript', flagship: false, status: 'built',
    blurb: 'Condition-gated branching dialogue + optional LLM free-talk, reusable in games.' },
  { id: 15, slug: '15-voice-assistant', name: 'Voice AI Assistant', theme: 'AI', stack: 'Python', flagship: false, status: 'built',
    blurb: 'STT→LLM→TTS pipeline with memory, barge-in, and per-stage latency tracking.' },
  { id: 16, slug: '16-semantic-code-search', name: 'Semantic Code Search', theme: 'AI', stack: 'Python', flagship: false, status: 'built',
    blurb: 'Search code by meaning; pluggable embedders, identifier-aware tokenizer.' },
  { id: 17, slug: '17-procedural-dungeon', name: 'Procedural Dungeon', theme: 'Games', stack: 'Rust · JS', flagship: false, status: 'built',
    blurb: 'Seeded BSP dungeon generator (Rust crate + JS port) with connectivity tests.' },
  { id: 18, slug: '18-physics-sandbox', name: 'Physics Sandbox', theme: 'Creative', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'Verlet-integration cloth with a deterministic, unit-tested physics core.' },
  { id: 19, slug: '19-retro-arcade', name: 'Gravity Snake', theme: 'Games', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'Snake with a twist — every apple flips gravity. Engine/render split.' },
  { id: 20, slug: '20-shader-gallery', name: 'Shader Gallery', theme: 'Creative', stack: 'WebGL', flagship: false, status: 'built',
    blurb: 'Animated GLSL fragment shaders: plasma, ripples, animated cell noise.' },
  { id: 21, slug: '21-level-editor', name: 'Level Editor', theme: 'Games', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'Tile editor exporting JSON levels; DOM-free tilemap model with flood fill.' },
  { id: 22, slug: '22-leaderboard-service', name: 'Leaderboard Service', theme: 'Games', stack: 'Go', flagship: false, status: 'built',
    blurb: 'Scores + achievements API with HMAC-signed submissions (anti-cheat).' },
  { id: 23, slug: '23-game-jam', name: 'One Button Ascent', theme: 'Games', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'A finished one-mechanic game-jam entry on the theme ONE BUTTON.' },
  { id: 24, slug: '24-kv-store', name: 'Persistent KV Store', theme: 'Systems', stack: 'Go', flagship: true, status: 'built',
    blurb: 'Bitcask-style WAL store: crash recovery, torn-tail handling, compaction.' },
  { id: 25, slug: '25-message-queue', name: 'Message Queue', theme: 'Systems', stack: 'Go', flagship: false, status: 'built',
    blurb: 'SQS-style at-least-once broker with visibility timeout and redelivery.' },
  { id: 26, slug: '26-rate-limiter', name: 'Rate Limiter + LB', theme: 'Systems', stack: 'Go', flagship: false, status: 'built',
    blurb: 'Token-bucket limiter + health-aware load balancer (round-robin/least-conn).' },
  { id: 27, slug: '27-observability', name: 'Observability', theme: 'Systems', stack: 'Python', flagship: false, status: 'built',
    blurb: 'Counter/gauge/histogram library with percentiles + Prometheus exposition.' },
  { id: 28, slug: '28-data-dashboard', name: 'Live Data Dashboard', theme: 'Full-stack', stack: 'Canvas', flagship: false, status: 'built',
    blurb: 'Streaming charts on a tested ring-buffer time-series core (WS-swappable).' },
  { id: 29, slug: '29-saas-starter', name: 'SaaS Starter', theme: 'Full-stack', stack: 'Go', flagship: false, status: 'built',
    blurb: 'Auth + webhook-driven subscription billing + feature gating by plan.' },
  { id: 30, slug: '30-portfolio-capstone', name: 'Portfolio Capstone', theme: 'Full-stack', stack: 'Static', flagship: true, status: 'built',
    blurb: 'This site — the front door indexing all 30 projects with live demos.' },
];

// Aggregate counts by theme, for the header summary.
export function themeCounts(projects = PROJECTS) {
  const counts = Object.fromEntries(THEMES.map((t) => [t, 0]));
  for (const p of projects) counts[p.theme] = (counts[p.theme] || 0) + 1;
  return counts;
}

export function filterProjects({ theme = 'All', flagshipOnly = false } = {}, projects = PROJECTS) {
  return projects.filter((p) => (theme === 'All' || p.theme === theme) && (!flagshipOnly || p.flagship));
}
