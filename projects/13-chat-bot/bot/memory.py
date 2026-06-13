"""Per-conversation short-term memory: a bounded ring buffer of turns so the
bot has context without unbounded growth."""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass


@dataclass
class Turn:
    role: str  # "user" or "assistant"
    content: str


class Memory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._chats: dict[str, deque[Turn]] = defaultdict(lambda: deque(maxlen=max_turns))

    def append(self, chat_id: str, role: str, content: str) -> None:
        self._chats[chat_id].append(Turn(role, content))

    def history(self, chat_id: str) -> list[Turn]:
        return list(self._chats.get(chat_id, []))

    def as_messages(self, chat_id: str) -> list[dict[str, str]]:
        return [{"role": t.role, "content": t.content} for t in self.history(chat_id)]

    def clear(self, chat_id: str) -> None:
        self._chats.pop(chat_id, None)
