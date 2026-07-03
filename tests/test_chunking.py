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
