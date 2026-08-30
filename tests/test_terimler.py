"""Gündelik dil → kanun terimi sözlüğü.

Ölçüm defalarca aynı şeyi gösterdi: kullanıcı "tahliye" diyor, kanun
"kiralananı boşaltma" diyor; kullanıcı "ev sahibi" diyor, kanun "kiraya veren"
diyor. Aynı sorular kanun diliyle sorulduğunda isabet ikiye katlanıyordu.

Bu çeviriyi modele yaptırmayı denedik ve ölçümde battı: model terim üretmek
yerine soruyu cevaplamaya kalkıp yanlış cümleler kurdu. Onun yerine elle
kurulmuş, dar ve korpustan doğrulanmış bir sözlük kullanılıyor.
"""
from app import store, terimler


def test_everyday_word_brings_the_statutory_term():
    genis = terimler.genislet("Tahliye taahhüdü verdim, ev sahibi beni çıkarabilir mi?")
    assert "boşalt" in genis.lower()
    assert "kiraya veren" in genis.lower()


def test_original_question_is_preserved():
    soru = "Ev sahibi kirayı ne kadar artırabilir?"
    assert soru in terimler.genislet(soru)


def test_rent_increase_reaches_the_statutory_phrase():
    genis = terimler.genislet("Ev sahibi kirayı ne kadar artırabilir?").lower()
    assert "kira bedeli" in genis


def test_consumer_words_are_mapped():
    genis = terimler.genislet("Aldığım ürün bozuk çıktı, iade edebilir miyim?").lower()
    assert "ayıplı mal" in genis
    assert "cayma hakkı" in genis


def test_question_without_a_known_term_is_untouched():
    soru = "Dava dilekçesinde neler bulunmak zorundadır?"
    assert terimler.genislet(soru) == soru


def test_a_term_already_in_the_question_is_not_repeated():
    genis = terimler.genislet("Kiraya veren kira bedelini artırabilir mi?")
    assert genis.lower().count("kiraya veren") == 1


def test_every_statutory_term_exists_in_the_corpus():
    """Sözlükteki hiçbir terim uydurulmuş olamaz; hepsi kanun metninde geçmeli.

    Yüklü korpus yoksa test atlanır (ingest edilmemiş ortam).
    """
    if store.count() == 0:
        import pytest
        pytest.skip("bilgi tabanı boş")
    tam = "\n".join(t.lower() for (_s, t, _e) in store.all_chunks())
    for _desen, kanun_terimleri in terimler.SOZLUK:
        for terim in kanun_terimleri:
            assert terim.lower() in tam, f"korpusta geçmiyor: {terim}"
