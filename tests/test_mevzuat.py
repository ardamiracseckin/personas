"""Kanun metnini madde bazlı parçalama.

Hukukta atıf, kaynağın kendisidir: "İş Kanunu md. 17" demek ile "bir yerde
okudum" demek arasındaki fark, kullanıcının hakkını arayıp arayamamasıdır. Bu
yüzden parçalama birimi paragraf değil **madde**dir ve her parça kendi kanun ve
madde numarasını taşır.

İki farklı yazım biçimi var ve ikisi de resmî: eski kanunlar "Madde 12 –",
2011 sonrası kanunlar "MADDE 12- (1)" kullanıyor.
"""
from app import mevzuat

YENI = """KİŞİSEL VERİLERİN KORUNMASI KANUNU
Kanun Numarası : 6698
Kabul Tarihi : 24/3/2016

Amaç
MADDE 1- (1) Bu Kanunun amacı, kişisel verilerin işlenmesini düzenlemektir.

Kapsam
MADDE 2- (1) Bu Kanun hükümleri, gerçek kişiler hakkında uygulanır.
(2) İkinci fıkra metni.
"""

ESKI = """İŞ KANUNU
Kanun Numarası : 4857
Kabul Tarihi : 22/5/2003

Amaç ve kapsam
Madde 1 - Bu Kanunun amacı işverenler ile işçilerin çalışma şartlarını düzenlemektir.

Tanımlar
Madde 2 - Bir iş sözleşmesine dayanarak çalışan gerçek kişiye işçi denir.
"""


def test_law_name_and_number_are_read_from_the_header():
    bilgi = mevzuat.kanun_bilgisi(YENI)
    assert bilgi.numara == "6698"
    assert "KİŞİSEL VERİLERİN KORUNMASI" in bilgi.ad


def test_new_style_articles_are_split():
    maddeler = mevzuat.maddeleri_ayir(YENI)
    assert [m.numara for m in maddeler] == ["1", "2"]


def test_old_style_articles_are_split():
    maddeler = mevzuat.maddeleri_ayir(ESKI)
    assert [m.numara for m in maddeler] == ["1", "2"]


def test_article_keeps_its_own_heading():
    # Madde başlığı ("Amaç") metnin üstündedir ve maddeye aittir.
    maddeler = mevzuat.maddeleri_ayir(YENI)
    assert maddeler[0].baslik == "Amaç"
    assert maddeler[1].baslik == "Kapsam"


def test_article_body_is_verbatim():
    # Hukukta özet yoktur: madde metni birebir korunmalı.
    maddeler = mevzuat.maddeleri_ayir(YENI)
    assert "kişisel verilerin işlenmesini düzenlemektir" in maddeler[0].metin


def test_all_paragraphs_of_an_article_stay_together():
    maddeler = mevzuat.maddeleri_ayir(YENI)
    assert "İkinci fıkra metni." in maddeler[1].metin


def test_chunks_carry_law_and_article_reference():
    parcalar = mevzuat.parcala(YENI, dosya="1.5.6698.pdf")
    assert parcalar[0].kanun_no == "6698"
    assert parcalar[0].madde == "1"
    assert parcalar[0].atif.startswith("6698 sayılı")
    assert "md. 1" in parcalar[0].atif


def test_amendment_markers_are_preserved():
    # "(Değişik:2/3/2024-7499/33 md.)" ibaresi maddenin hangi tarihli hâli
    # olduğunu söyler; silinirse kullanıcı güncelliği doğrulayamaz.
    metin = YENI.replace("MADDE 2- (1) Bu Kanun",
                         "MADDE 2- (1) (Değişik:2/3/2024-7499/33 md.) Bu Kanun")
    parcalar = mevzuat.parcala(metin, dosya="x.pdf")
    assert "(Değişik:2/3/2024-7499/33 md.)" in parcalar[1].metin


# --- ek ve geçici maddeler ---------------------------------------------------

EKLI = """İŞ KANUNU
Kanun Numarası : 4857

Bir madde
Madde 5 - Normal madde metni.

Ek Madde 1 - Ek madde metni.

Geçici Madde 3 - Geçici madde metni.
"""


def test_additional_and_temporary_articles_are_recognised():
    maddeler = mevzuat.maddeleri_ayir(EKLI)
    assert [m.numara for m in maddeler] == ["5", "Ek 1", "Geçici 3"]


def test_temporary_article_citation_is_unambiguous():
    parcalar = mevzuat.parcala(EKLI)
    gecici = [p for p in parcalar if p.madde == "Geçici 3"][0]
    assert "md. Geçici 3" in gecici.atif


# --- uzun maddelerin bölünmesi -----------------------------------------------

def _uzun_kanun(fikra_sayisi=12):
    fikralar = "\n".join(f"({i}) " + ("Bu fıkranın metni yeterince uzundur. " * 6)
                         for i in range(1, fikra_sayisi + 1))
    return f"UZUN KANUN\nKanun Numarası : 9999\n\nBaşlık\nMADDE 1- {fikralar}\n"


def test_long_articles_are_split_into_pieces():
    parcalar = mevzuat.parcala(_uzun_kanun(), max_chars=600)
    assert len(parcalar) > 1
    assert all(len(p.metin) <= 700 for p in parcalar)


def test_every_piece_keeps_the_same_article_reference():
    parcalar = mevzuat.parcala(_uzun_kanun(), max_chars=600)
    assert {p.madde for p in parcalar} == {"1"}
    assert all("md. 1" in p.atif for p in parcalar)


def test_pieces_are_numbered_so_the_reader_knows_it_is_partial():
    parcalar = mevzuat.parcala(_uzun_kanun(), max_chars=600)
    assert parcalar[0].parca_no == 1
    assert parcalar[1].parca_no == 2


def test_splitting_loses_no_text():
    kanun = _uzun_kanun()
    parcalar = mevzuat.parcala(kanun, max_chars=600)
    birlesik = " ".join(" ".join(p.metin.split()) for p in parcalar)
    for i in range(1, 13):
        assert f"({i})" in birlesik


def test_short_articles_are_not_split():
    parcalar = mevzuat.parcala(YENI, max_chars=600)
    assert all(p.parca_no == 1 for p in parcalar)


# --- Türkçe başlık biçimlendirme ---------------------------------------------

def test_turkish_title_case_handles_dotted_and_dotless_i():
    # Python'un .title() metodu Türkçe bilmez: "İ".lower() birleşik nokta üretir
    # ("i̇") ve "I".lower() "i" verir, "ı" değil. Kanun adları bu yüzden bozuluyordu.
    assert mevzuat.turkce_baslik("KARAYOLLARI TRAFİK KANUNU") == "Karayolları Trafik Kanunu"
    assert mevzuat.turkce_baslik("TÜRK MEDENİ KANUNU") == "Türk Medeni Kanunu"
    assert mevzuat.turkce_baslik("TÜKETİCİNİN KORUNMASI HAKKINDA KANUN") == \
        "Tüketicinin Korunması Hakkında Kanun"


def test_turkish_title_case_keeps_short_words_lowercase():
    assert mevzuat.turkce_baslik("İŞ MAHKEMELERİ KANUNU") == "İş Mahkemeleri Kanunu"


def test_uppercase_temporary_article_is_not_confused_with_a_normal_one():
    """GEÇİCİ MADDE 2 ile MADDE 2 bambaşka hükümlerdir.

    Bu hata gerçekten oluştu: "GEÇİCİ".lower() Python'da "geçi̇ci̇" veriyor
    (birleşik noktalı i), sözlük araması tutmuyordu ve geçici madde normal madde
    gibi atıf alıyordu. Hukukta bu, yanlış hükme gönderme demektir.
    """
    metin = ("KANUN\nKanun Numarası : 6098\n\n"
             "MADDE 2- Normal ikinci madde.\n\n"
             "GEÇİCİ MADDE 2- (Ek: 14/7/2023-7456/23 md.) Konut kiralarına ilişkin geçici hüküm.\n")
    numaralar = [m.numara for m in mevzuat.maddeleri_ayir(metin)]
    assert numaralar == ["2", "Geçici 2"]


def test_uppercase_additional_article_is_recognised():
    metin = "KANUN\nKanun Numarası : 4857\n\nEK MADDE 1 - Ek hüküm.\n"
    assert [m.numara for m in mevzuat.maddeleri_ayir(metin)] == ["Ek 1"]
