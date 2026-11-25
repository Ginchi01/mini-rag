"""单元测试：只测纯函数，不依赖 Ollama，所以能离线跑、能进 CI。"""
from app.chunker import split_text


def test_empty_text():
    assert split_text("", "a.md") == []
    assert split_text("   \n  ", "a.md") == []


def test_single_short_chunk_is_dropped():
    # 小于 min_len 的碎片应该被丢掉
    assert split_text("短", "a.md", size=400, overlap=60, min_len=30) == []


def test_overlap_makes_chunks_share_text():
    text = "甲" * 1000
    chunks = split_text(text, "a.md", size=400, overlap=60, min_len=1)
    assert len(chunks) == 3
    # 相邻块起始位置相差 size - overlap
    assert chunks[1].start - chunks[0].start == 340


def test_no_infinite_loop_on_exact_boundary():
    text = "b" * 400
    chunks = split_text(text, "a.md", size=400, overlap=60, min_len=1)
    assert len(chunks) == 1


def test_source_is_recorded():
    chunks = split_text("c" * 500, "骨龄.md", size=400, overlap=60, min_len=1)
    assert all(c.source == "骨龄.md" for c in chunks)


def test_invalid_params():
    import pytest
    with pytest.raises(ValueError):
        split_text("x" * 100, "a.md", size=0)
    with pytest.raises(ValueError):
        split_text("x" * 100, "a.md", size=100, overlap=100)
