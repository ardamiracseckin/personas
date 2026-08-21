"""Sözlüksel eşleşme: Türkçe sadeleştirme ve yazım hatasına dayanıklılık."""
import pytest

from app import lexical


@pytest.mark.parametrize("ham,beklenen", [
    ("Görüntüsünü ALDIM", "goruntusunu aldim"),
    ("İşte, şu ÇOK güzel!", "iste su cok guzel"),
    ("ığdır ĞÜŞİÖÇ", "igdir gusioc"),
    ("git reset --soft HEAD~1", "git reset soft head 1"),
])
def test_normalize(ham, beklenen):
    assert lexical.normalize(ham) == beklenen


def test_tokens_drops_filler_but_keeps_content():
    assert lexical.tokens("bir de ekran görüntüsü") == ["ekran", "goruntusu"]


def test_typo_query_matches_the_right_text():
    metin = "Ekran görüntüsü (belirli bölge): Cmd + Shift + 4 tuşlarına basılır."
    bozuk = "ekran görünütsünü belirli bölgden nasıl alrım"
    temiz = "ekran görüntüsünü belirli bölgeden nasıl alırım"
    assert lexical.fuzzy_score(bozuk, metin) > 0.5
    # Bozuk yazım, temiz yazımın çok altına düşmemeli
    assert lexical.fuzzy_score(bozuk, metin) >= lexical.fuzzy_score(temiz, metin) - 0.2


def test_unrelated_text_scores_zero():
    assert lexical.fuzzy_score("kubernetes pod silme", "Cmd + Shift + 4 ekran görüntüsü") == 0.0


def test_score_is_bounded():
    metin = "git stash ile değişiklikler saklanır"
    assert 0.0 <= lexical.fuzzy_score("git stash", metin) <= 1.0
    assert lexical.fuzzy_score("", metin) == 0.0


def test_two_letter_commands_are_kept():
    # "ls -la" gibi sorgularda tüm bilgi iki harfli kelimelerde.
    assert lexical.tokens("ls -la") == ["ls", "la"]
    assert lexical.fuzzy_score("ls -la", "Gizli dosyalar için `ls -la` kullanılır.") == 1.0


def test_filler_words_are_dropped():
    assert lexical.tokens("bu ve da ki için ekran") == ["ekran"]
