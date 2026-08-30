"""Gövde bazlı BM25 — kelime düzeyinde erişim.

Kanun metninde ayırt edici terimler birebir geçer: "tahliye taahhüdü", "cayma
hakkı", "arabuluculuk". Ama Türkçe eklemeli bir dil olduğu için sorgudaki
"tahliye taahhüdü" ile kanundaki "tahliye taahhüdünü" tam kelime olarak
tutmaz. Ölçüm bunu gösterdi: tam kelimeyle BM25 hit@1 1/10, gövdeyle 2/10,
kosinüsle harmanlanınca 4/10 (kosinüs tek başına 2/10).

Gövde uzunluğu 5 karakter olarak ölçümle seçildi.
"""
from app import bm25


BELGELER = [
    "Kiracı yazılı tahliye taahhüdünde bulunmuşsa icra yoluyla tahliye istenebilir.",
    "Tüketici on dört gün içinde cayma hakkını kullanabilir.",
    "Yıllık ücretli izin süreleri hizmet süresine göre belirlenir.",
]


def test_index_finds_the_document_with_the_distinctive_term():
    dizin = bm25.Dizin(BELGELER)
    puanlar = dizin.puanla("tahliye taahhüdü verdim ne olur")
    assert max(puanlar, key=puanlar.get) == 0


def test_suffixes_do_not_break_the_match():
    """Sorguda 'taahhüdü', metinde 'taahhüdünde' — gövde ikisini de yakalar."""
    dizin = bm25.Dizin(BELGELER)
    assert dizin.puanla("tahliye taahhüdü").get(0, 0) > 0


def test_unrelated_query_scores_nothing():
    dizin = bm25.Dizin(BELGELER)
    assert not dizin.puanla("docker konteyner kurulumu")


def test_normalisation_keeps_absolute_magnitude():
    """Sorgu içi maksimuma bölmek yanlıştı: alakasız bir soruda bile bir parça
    1.0 alıyor ve "bilmiyorum" diyebilme özelliği kırılıyordu. Ölçüm ham puanları
    ayırt edilebilir buldu — ilgili sorularda 10-19, alakasızlarda 7-9,6 — bu
    yüzden sabit bir doyum değerine bölünür.
    """
    dizin = bm25.Dizin(BELGELER)
    puanlar = dizin.normalize("cayma hakkı")
    assert all(0.0 <= p <= 1.0 for p in puanlar.values())
    # Küçük bir örnekte hiçbir parça doyuma ulaşmaz.
    assert max(puanlar.values()) < 1.0


def test_a_stronger_match_scores_higher_than_a_weaker_one():
    dizin = bm25.Dizin(BELGELER)
    guclu = max(dizin.normalize("tahliye taahhüdü icra").values())
    zayif = max(dizin.normalize("süre").values() or [0.0])
    assert guclu > zayif


def test_empty_corpus_is_safe():
    assert bm25.Dizin([]).puanla("herhangi bir sorgu") == {}
