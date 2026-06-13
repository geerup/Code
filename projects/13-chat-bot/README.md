# 💬 LLM Chat-Bot (#13)

A deployable messaging bot powered by a local Ollama model. Receives Telegram
webhook updates, keeps **per-conversation memory**, handles slash commands, and
replies — all from a single stdlib `http.server` process (no third-party deps).

## Architecture
- `bot/core.py` — platform-agnostic `Bot.handle(IncomingMessage) -> str`, with
  memory + `/start`, `/help`, `/reset` commands.
- `bot/memory.py` — bounded ring buffer per chat (context without unbounded growth).
- `bot/telegram.py` — pure parse/format functions for the Telegram API.
- `bot/llm.py` — `OllamaLLM` for real use, `EchoLLM` for tests.
- `server.py` — webhook endpoint + health check; `Dockerfile` → Fly worker.

Adapters only translate payloads, so adding Discord is a new ~20-line module.

## Run
```bash
python -m unittest discover -s tests                 # offline
TELEGRAM_TOKEN=xxx python server.py                  # then set Telegram webhook -> /webhook
```
Without a token the server runs in dry-run mode (prints outgoing messages).

## What I learned / next
- Webhook plumbing, multi-turn memory, keeping a core decoupled from platforms.
- Next: a Discord gateway adapter, streaming "typing…" indicators, and
  persisting memory to SQLite so it survives restarts.
