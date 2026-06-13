import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from voice import VoiceAssistant, FakeSTT, EchoLLM, FakeTTS  # noqa: E402


def make_assistant():
    return VoiceAssistant(FakeSTT(), EchoLLM(), FakeTTS())


class TestPipeline(unittest.TestCase):
    def test_full_turn(self):
        va = make_assistant()
        result = va.handle_turn(b"hello assistant")
        self.assertEqual(result.transcript, "hello assistant")
        self.assertEqual(result.reply, "You said: hello assistant")
        self.assertEqual(result.audio, b"WAV:You said: hello assistant")

    def test_empty_transcript_short_circuits(self):
        va = VoiceAssistant(FakeSTT({b"\x00\x01": ""}), EchoLLM(), FakeTTS())
        result = va.handle_turn(b"\x00\x01")
        self.assertEqual(result.reply, "")
        self.assertEqual(result.audio, b"")
        self.assertEqual(va.history, [])  # nothing recorded

    def test_memory_accumulates(self):
        va = make_assistant()
        va.handle_turn(b"first")
        va.handle_turn(b"second")
        contents = [m["content"] for m in va.history]
        self.assertIn("first", contents)
        self.assertIn("second", contents)

    def test_memory_is_trimmed(self):
        va = VoiceAssistant(FakeSTT(), EchoLLM(), FakeTTS(), max_turns=4)
        for i in range(10):
            va.handle_turn(str(i).encode())
        self.assertLessEqual(len(va.history), 4)

    def test_barge_in_skips_tts(self):
        va = make_assistant()
        result = va.handle_turn(b"interrupt me", is_cancelled=lambda: True)
        self.assertTrue(result.cancelled)
        self.assertEqual(result.audio, b"")          # no speech produced
        self.assertEqual(result.reply, "You said: interrupt me")  # but reply computed

    def test_timings_recorded(self):
        # Deterministic fake clock advancing 1ms per call.
        ticks = iter(range(0, 100))
        va = make_assistant()
        va.set_clock(lambda: next(ticks) / 1000.0)
        result = va.handle_turn(b"timing")
        self.assertIn("stt", result.timings_ms)
        self.assertIn("llm", result.timings_ms)
        self.assertIn("tts", result.timings_ms)
        self.assertIn("total", result.timings_ms)


if __name__ == "__main__":
    unittest.main()
