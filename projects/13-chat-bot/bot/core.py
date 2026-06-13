"""Platform-agnostic bot core: turn an incoming message into a reply, with
memory and slash-command handling. Platform adapters (Telegram, Discord) only
translate payloads to/from this core."""
from __future__ import annotations

from dataclasses import dataclass

from .llm import LLM
from .memory import Memory

DEFAULT_PERSONA = (
    "You are a helpful, concise assistant chatting in a messaging app. "
    "Keep replies short and friendly."
)


@dataclass
class IncomingMessage:
    chat_id: str
    text: str
    user: str = ""


class Bot:
    def __init__(self, llm: LLM, persona: str = DEFAULT_PERSONA, max_turns: int = 10):
        self.llm = llm
        self.persona = persona
        self.memory = Memory(max_turns)

    def handle(self, msg: IncomingMessage) -> str:
        text = msg.text.strip()

        # Slash commands handled locally, no model call.
        if text in ("/start", "/help"):
            return "👋 Hi! I'm an LLM-powered bot. Just send a message. /reset clears our chat."
        if text == "/reset":
            self.memory.clear(msg.chat_id)
            return "🧹 Conversation cleared."

        self.memory.append(msg.chat_id, "user", text)
        messages = [{"role": "system", "content": self.persona}] + self.memory.as_messages(msg.chat_id)
        reply = self.llm.chat(messages)
        self.memory.append(msg.chat_id, "assistant", reply)
        return reply
