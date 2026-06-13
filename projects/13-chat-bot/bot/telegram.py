"""Telegram adapter: parse a webhook update into an IncomingMessage and build
the sendMessage reply payload. Pure functions so they're unit-testable without
hitting Telegram."""
from __future__ import annotations

from .core import IncomingMessage


def parse_update(update: dict) -> IncomingMessage | None:
    """Telegram sends {"message": {"chat": {"id": ...}, "text": ...}}."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return None
    chat = message.get("chat", {})
    text = message.get("text")
    if text is None or "id" not in chat:
        return None
    user = (message.get("from") or {}).get("username", "")
    return IncomingMessage(chat_id=str(chat["id"]), text=text, user=user)


def reply_payload(chat_id: str, text: str) -> dict:
    """Body for Telegram's sendMessage method."""
    return {"chat_id": chat_id, "text": text}
