from app.chunking import chunk_text


def test_splits_on_blank_lines_and_packs():
    text = "Para one.\n\nPara two.\n\nPara three."
    # max_chars=10 is smaller than any two paras combined, so each stays separate.
    chunks = chunk_text(text, max_chars=10)
    assert chunks == ["Para one.", "Para two.", "Para three."]


def test_packs_small_paras_together():
    text = "aa\n\nbb\n\ncc"
    assert chunk_text(text, max_chars=100) == ["aa\n\nbb\n\ncc"]


def test_ignores_empty_input():
    assert chunk_text("   \n\n  ") == []


def test_chunk_carries_its_heading():
    text = "# Başlık\n\n## Bölüm A\n\nBirinci paragraf.\n\nİkinci paragraf."
    chunks = chunk_text(text, max_chars=200)
    # Tek bölüm, tek parça: başlık ve iki paragraf birlikte.
    assert len(chunks) == 1
    assert chunks[0].startswith("## Bölüm A")
    assert "Birinci paragraf." in chunks[0]


def test_new_heading_starts_new_chunk():
    text = "## Bölüm A\n\naaa\n\n## Bölüm B\n\nbbb"
    chunks = chunk_text(text, max_chars=500)
    assert len(chunks) == 2
    assert chunks[0].startswith("## Bölüm A") and "aaa" in chunks[0]
    assert chunks[1].startswith("## Bölüm B") and "bbb" in chunks[1]


def test_long_section_splits_but_keeps_heading_on_each_part():
    text = "## Uzun Bölüm\n\n" + "\n\n".join(["p" * 40 for _ in range(6)])
    chunks = chunk_text(text, max_chars=120)
    assert len(chunks) > 1
    assert all(c.startswith("## Uzun Bölüm") for c in chunks)
    assert all(len(c) <= 120 for c in chunks)
