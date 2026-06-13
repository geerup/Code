from app.embeddings import FakeEmbeddings
from app.store import VectorStore


def make_store(tmp_path):
    return VectorStore(str(tmp_path / "test.db"))


def test_add_and_list_documents(tmp_path):
    store = make_store(tmp_path)
    emb = FakeEmbeddings()
    chunks = ["the cat sat on the mat", "dogs love to run in the park"]
    store.add_document("animals.txt", chunks, emb.embed(chunks))

    docs = store.list_documents()
    assert len(docs) == 1
    assert docs[0]["source"] == "animals.txt"
    assert docs[0]["chunk_count"] == 2


def test_search_returns_nearest_chunk(tmp_path):
    store = make_store(tmp_path)
    emb = FakeEmbeddings()
    chunks = [
        "python is a programming language for data science",
        "the eiffel tower is located in paris france",
        "basketball is played with an orange ball",
    ]
    store.add_document("mixed.txt", chunks, emb.embed(chunks))

    query = emb.embed(["which programming language is used for data science"])[0]
    hits = store.search(query, top_k=1)
    assert len(hits) == 1
    assert "programming language" in hits[0].text


def test_search_empty_store_returns_empty(tmp_path):
    store = make_store(tmp_path)
    query = FakeEmbeddings().embed(["anything"])[0]
    assert store.search(query, top_k=4) == []


def test_mismatched_lengths_raise(tmp_path):
    store = make_store(tmp_path)
    try:
        store.add_document("x", ["a", "b"], [[0.1]])
    except ValueError:
        return
    raise AssertionError("expected ValueError for mismatched lengths")
