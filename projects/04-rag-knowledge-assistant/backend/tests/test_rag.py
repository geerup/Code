from app.config import Settings
from app.embeddings import FakeEmbeddings
from app.llm import FakeChat
from app.rag import RAGService, build_prompt
from app.store import SearchHit, VectorStore


def make_service(tmp_path):
    settings = Settings(
        db_path=str(tmp_path / "rag.db"), embed_provider="fake", llm_provider="fake"
    )
    store = VectorStore(settings.db_path)
    return RAGService(store, FakeEmbeddings(), FakeChat(), settings)


def test_build_prompt_numbers_and_cites_passages():
    hits = [
        SearchHit(1, 1, "a.txt", "first passage", 0.9),
        SearchHit(2, 1, "b.txt", "second passage", 0.8),
    ]
    prompt = build_prompt("what is this?", hits)
    assert "[1]" in prompt and "[2]" in prompt
    assert "source: a.txt" in prompt
    assert "Question: what is this?" in prompt


def test_build_prompt_handles_no_hits():
    prompt = build_prompt("anything", [])
    assert "(none)" in prompt


def test_ingest_then_answer_end_to_end(tmp_path):
    service = make_service(tmp_path)
    result = service.ingest("doc.txt", "Retrieval augmented generation grounds answers in sources.")
    assert result["chunks"] >= 1

    citations, stream = service.answer_stream("what does RAG do?")
    assert len(citations) >= 1
    assert citations[0].index == 1
    text = "".join(stream)
    assert text.strip() != ""


def test_ingest_empty_document_raises(tmp_path):
    service = make_service(tmp_path)
    try:
        service.ingest("empty.txt", "   ")
    except ValueError:
        return
    raise AssertionError("expected ValueError for empty document")
