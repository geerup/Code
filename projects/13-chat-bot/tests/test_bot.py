import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot import Bot, EchoLLM, IncomingMessage, Memory, telegram  # noqa: E402


class TestMemory(unittest.TestCase):
    def test_ring_buffer_bounds(self):
        m = Memory(max_turns=4)
        for i in range(10):
            m.append("c1", "user", str(i))
        self.assertEqual(len(m.history("c1")), 4)
        self.assertEqual(m.history("c1")[-1].content, "9")

    def test_chats_are_isolated(self):
        m = Memory()
        m.append("a", "user", "hi")
        self.assertEqual(m.history("b"), [])


class TestBot(unittest.TestCase):
    def test_reply_uses_llm(self):
        bot = Bot(EchoLLM())
        out = bot.handle(IncomingMessage("c1", "hello"))
        self.assertEqual(out, "echo: hello")

    def test_memory_accumulates_across_turns(self):
        llm = EchoLLM()
        bot = Bot(llm)
        bot.handle(IncomingMessage("c1", "first"))
        bot.handle(IncomingMessage("c1", "second"))
        # Second call should include prior turns + system persona.
        last_messages = llm.seen[-1]
        roles = [m["role"] for m in last_messages]
        self.assertEqual(roles[0], "system")
        contents = [m["content"] for m in last_messages]
        self.assertIn("first", contents)
        self.assertIn("second", contents)

    def test_reset_command_clears_memory(self):
        bot = Bot(EchoLLM())
        bot.handle(IncomingMessage("c1", "remember this"))
        out = bot.handle(IncomingMessage("c1", "/reset"))
        self.assertIn("cleared", out.lower())
        self.assertEqual(bot.memory.history("c1"), [])

    def test_help_command_no_model_call(self):
        llm = EchoLLM()
        bot = Bot(llm)
        out = bot.handle(IncomingMessage("c1", "/help"))
        self.assertIn("bot", out.lower())
        self.assertEqual(llm.seen, [])  # no LLM call for slash commands


class TestTelegramAdapter(unittest.TestCase):
    def test_parse_valid_update(self):
        msg = telegram.parse_update({"message": {"chat": {"id": 42}, "text": "yo", "from": {"username": "ann"}}})
        self.assertEqual(msg.chat_id, "42")
        self.assertEqual(msg.text, "yo")
        self.assertEqual(msg.user, "ann")

    def test_parse_ignores_non_message_updates(self):
        self.assertIsNone(telegram.parse_update({"poll": {}}))
        self.assertIsNone(telegram.parse_update({"message": {"chat": {"id": 1}}}))  # no text

    def test_reply_payload_shape(self):
        self.assertEqual(telegram.reply_payload("9", "hi"), {"chat_id": "9", "text": "hi"})


if __name__ == "__main__":
    unittest.main()
