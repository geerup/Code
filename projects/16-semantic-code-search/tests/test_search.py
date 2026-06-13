import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from codesearch import HashingEmbedder, Index, cosine, tokenize, chunk_text  # noqa: E402


class TestTokenize(unittest.TestCase):
    def test_splits_camel_and_snake_case(self):
        toks = tokenize("getUserName user_id")
        self.assertIn("get", toks)
        self.assertIn("user", toks)
        self.assertIn("name", toks)
        self.assertIn("id", toks)


class TestEmbedder(unittest.TestCase):
    def test_deterministic(self):
        e = HashingEmbedder(128)
        self.assertEqual(e.embed("hello world"), e.embed("hello world"))

    def test_normalized(self):
        e = HashingEmbedder(128)
        v = e.embed("some code about parsing tokens")
        norm = sum(x * x for x in v) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=5)

    def test_cosine_self_is_one(self):
        e = HashingEmbedder(128)
        v = e.embed("parse the diff")
        self.assertAlmostEqual(cosine(v, v), 1.0, places=5)


class TestChunking(unittest.TestCase):
    def test_chunk_line_ranges(self):
        text = "\n".join(f"line{i}" for i in range(100))
        chunks = chunk_text(text, "f.py", window=30, stride=20)
        self.assertEqual(chunks[0].start_line, 1)
        self.assertTrue(all(c.path == "f.py" for c in chunks))
        self.assertGreater(len(chunks), 1)


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.index = Index(HashingEmbedder(512))
        self.index.add_text(
            "def parse_unified_diff(text):\n    # split hunks and lines\n    return hunks",
            "diff.py",
        )
        self.index.add_text(
            "def cosine_similarity(a, b):\n    # dot product over norms\n    return dot/(na*nb)",
            "vec.py",
        )
        self.index.add_text(
            "class HttpServer:\n    def serve(self):\n        listen on a socket",
            "server.py",
        )

    def test_relevant_file_ranks_first(self):
        hits = self.index.search("parse the diff hunks", k=3)
        self.assertEqual(hits[0].path, "diff.py")

    def test_cosine_query_finds_vector_file(self):
        hits = self.index.search("cosine similarity dot product norm", k=3)
        self.assertEqual(hits[0].path, "vec.py")

    def test_k_limits_results(self):
        self.assertEqual(len(self.index.search("anything", k=2)), 2)


if __name__ == "__main__":
    unittest.main()
