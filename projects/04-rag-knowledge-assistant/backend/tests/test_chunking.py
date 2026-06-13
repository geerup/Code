from app.chunking import chunk_text, normalize


def test_normalize_collapses_whitespace():
    assert normalize("a   b\t\tc") == "a b c"
    assert normalize("a\n\n\n\nb") == "a\n\nb"


def test_empty_text_yields_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_text_is_single_chunk():
    chunks = chunk_text("hello world", chunk_size=800)
    assert chunks == ["hello world"]


def test_long_text_splits_into_multiple_chunks():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = chunk_text(text, chunk_size=100, overlap=20)
    assert len(chunks) > 1
    assert all(len(c) <= 100 for c in chunks)


def test_chunks_overlap_for_context_continuity():
    text = " ".join(f"w{i}" for i in range(200))
    chunks = chunk_text(text, chunk_size=80, overlap=30)
    # The tail of one chunk should reappear at the head of the next.
    first_tail = chunks[0].split()[-1]
    assert first_tail in chunks[1].split()


def test_words_are_never_split():
    text = "supercalifragilistic " * 20
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    for c in chunks:
        for word in c.split():
            assert word == "supercalifragilistic"


def test_overlap_is_clamped_below_chunk_size():
    # overlap >= chunk_size must still make forward progress, not loop forever.
    chunks = chunk_text("a b c d e f g h", chunk_size=5, overlap=99)
    assert len(chunks) >= 1
