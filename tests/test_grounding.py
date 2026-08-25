"""Sadakat ölçümü: cevap getirilen parçaya mı dayanıyor, modelin ezberine mi?"""
from app import grounding

BAGLAM = ["## Stash — geçici saklama\n\nYarım kalan değişiklikleri geçici olarak saklamak için "
          "`git stash` çalıştırılır. Geri getirmek için `git stash pop` kullanılır."]


def test_answer_taken_from_context_scores_high():
    cevap = "Değişiklikleri geçici saklamak için `git stash`, geri getirmek için `git stash pop`."
    assert grounding.score(cevap, BAGLAM) > 0.8


def test_answer_from_outside_the_context_scores_low():
    cevap = "Docker konteynerlerini yönetmek için `docker compose up` komutunu kullanabilirsin."
    assert grounding.score(cevap, BAGLAM) < 0.3


def test_question_words_do_not_inflate_the_score():
    # Soruyu tekrarlamak dayanak sayılmaz: aynı uydurma cevap, başına sorunun
    # kelimeleri eklendiğinde daha yüksek puan almamalı.
    soru = "Yarım kalan değişiklikleri geçici olarak nasıl saklarım?"
    uydurma = "Docker konteynerini yeniden başlat."
    tekrarli = "Yarım kalan değişiklikleri geçici olarak: Docker konteynerini yeniden başlat."
    assert grounding.score(tekrarli, BAGLAM, question=soru) == \
        grounding.score(uydurma, BAGLAM, question=soru)


def test_empty_inputs_are_safe():
    assert grounding.score("", BAGLAM) == 0.0
    assert grounding.score("herhangi bir cevap", []) == 0.0


def test_unsupported_tokens_are_reported():
    cevap = "`git stash` kullan, sonra Docker konteynerini yeniden başlat."
    dayanaksiz = grounding.unsupported_tokens(cevap, BAGLAM)
    assert "docker" in dayanaksiz
    assert "stash" not in dayanaksiz


def test_abstention_is_not_penalised():
    # "Bilgim yok" cevabı bağlama dayanmaz ama uydurma da değildir.
    assert grounding.score("Belgelerimde bu konuda bilgi yok.", BAGLAM) is None


# --- modelin kendi cümle kurma kelimeleri ------------------------------------

LS_BAGLAM = ["Gizli dosyaları da listelemek için `ls -la` yazılır."]


def test_the_models_own_wording_is_not_counted_as_invention():
    # "komutunu kullanın" bağlamda geçmez ama uydurma da değildir; ölçüt bunu
    # cezalandırırsa doğru cevaplar düşük sadakatli görünür.
    assert grounding.score("`ls -la` komutunu kullanın.", LS_BAGLAM) > 0.9


def test_glue_words_do_not_hide_a_made_up_command():
    assert grounding.score("`docker ps` komutunu kullanın.", LS_BAGLAM) < 0.4


# --- kod sadakati: uydurulmuş komut var mı -----------------------------------

def test_command_taken_from_the_context_is_supported():
    assert grounding.unsupported_code_spans("Şunu yaz: `ls -la`", LS_BAGLAM) == []


def test_invented_command_is_reported_even_when_the_prose_is_grounded():
    cevap = "Gizli dosyaları da listelemek için `ls --hidden` yazılır."
    assert grounding.unsupported_code_spans(cevap, LS_BAGLAM) == ["ls --hidden"]


def test_spacing_differences_do_not_count_as_invention():
    baglam = ["Bölge seçerek ekran görüntüsü: `Cmd + Shift + 4`."]
    assert grounding.unsupported_code_spans("`Cmd+Shift+4` tuşlarına bas.", baglam) == []
