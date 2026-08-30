"""Mevzuat yanıtı: üretmez, çıkarır.

Ölçüm gösterdi ki bu boyuttaki yerel modeller Türkçe hukuk metninde yanlış
cümleler kuruyor ("arabulucuya gitmek zorunlu değildir" gibi). Bu yüzden
asistan cevabı ÜRETMEZ. Getirilen maddenin kendi cümlelerinden soruya en yakın
olanı seçip öne alır — ekranda görünen her kelime kanun metnindendir.
"""
from app import mevzuat_yanit

MADDE = ("6502 sayılı Tüketicinin Korunması Hakkında Kanun md. 48 — Mesafeli sözleşmeler\n\n"
         "MADDE 48- (1) Mesafeli sözleşme, satıcı veya sağlayıcı ile tüketicinin eş zamanlı "
         "fiziksel varlığı olmaksızın kurulan sözleşmelerdir. "
         "(2) Tüketici, on dört gün içinde herhangi bir gerekçe göstermeksizin ve cezai şart "
         "ödemeksizin sözleşmeden cayma hakkına sahiptir. "
         "(3) Cayma hakkının kullanıldığına dair bildirimin bu süre içinde yöneltilmesi yeterlidir.")

DIGER = ("4857 sayılı İş Kanunu md. 17 — Süreli fesih\n\n"
         "Madde 17 - Belirsiz süreli iş sözleşmelerinin feshinden önce bildirim yapılır.")


def test_the_most_relevant_sentence_is_extracted():
    yanit = mevzuat_yanit.hazirla("Kaç gün içinde cayabilirim?", [(MADDE, 0.7)])
    assert "on dört gün" in yanit.birincil.one_cikan
    assert "cayma hakkına sahiptir" in yanit.birincil.one_cikan


def test_extracted_sentence_is_verbatim_from_the_article():
    yanit = mevzuat_yanit.hazirla("Kaç gün içinde cayabilirim?", [(MADDE, 0.7)])
    assert yanit.birincil.one_cikan in " ".join(MADDE.split())


def test_citation_and_heading_are_kept_separate_from_the_text():
    yanit = mevzuat_yanit.hazirla("cayma", [(MADDE, 0.7)])
    assert yanit.birincil.atif == "6502 sayılı Tüketicinin Korunması Hakkında Kanun md. 48"
    assert yanit.birincil.baslik == "Mesafeli sözleşmeler"
    assert "md. 48" not in yanit.birincil.metin


def test_candidates_keep_the_retrieval_order():
    yanit = mevzuat_yanit.hazirla("cayma", [(MADDE, 0.7), (DIGER, 0.4)])
    assert yanit.birincil.atif.startswith("6502")
    assert [a.atif.split(" sayılı")[0] for a in yanit.digerleri] == ["4857"]


def test_no_candidate_means_no_invented_answer():
    yanit = mevzuat_yanit.hazirla("Bugün hava nasıl?", [])
    assert yanit.birincil is None
    assert yanit.digerleri == []
    assert yanit.bulunamadi is True


def test_scores_are_carried_for_transparency():
    yanit = mevzuat_yanit.hazirla("cayma", [(MADDE, 0.73)])
    assert yanit.birincil.puan == 0.73


# --- erişimle birleşme -------------------------------------------------------

def test_pipeline_returns_ranked_candidates(monkeypatch):
    """Asistan mevzuat kipinde model çağırmaz; erişip çıkarır."""
    from app import mevzuat_yanit as my, retriever

    monkeypatch.setattr(retriever, "get_top_chunks",
                        lambda q, k=None, embed_fn=None, **_: [("6502 sayılı X md. 48 — Mesafeli\n\nMADDE 48- (1) On dört gün içinde cayma hakkı vardır.", 0.7),
                                                          ("4857 sayılı Y md. 17 — Fesih\n\nMadde 17 - Bildirim süresi.", 0.4)])
    yanit = my.sor("Kaç gün içinde cayabilirim?")
    assert yanit.birincil.atif.startswith("6502")
    assert len(yanit.digerleri) == 1


def test_pipeline_reports_when_nothing_passes_the_threshold(monkeypatch):
    from app import mevzuat_yanit as my, retriever

    monkeypatch.setattr(retriever, "get_top_chunks", lambda q, k=None, embed_fn=None, **_: [])
    assert my.sor("Bugün hava nasıl?").bulunamadi is True


# --- aynı madde listeyi işgal etmesin ---------------------------------------

def _parca(kanun, madde, bolum, metin, puan):
    ek = f" ({bolum})" if bolum else ""
    return (f"{kanun} md. {madde} — Başlık{ek}\n\n{metin}", puan)


def test_pieces_of_the_same_article_are_merged():
    """Uzun bir madde beş parçaya bölünmüşse liste beş sırasını ona harcamamalı."""
    parcalar = [_parca("7036 sayılı X", "3", "1/9", "Birinci bölüm metni.", 0.54),
                _parca("7036 sayılı X", "3", "5/9", "Beşinci bölüm metni.", 0.53),
                _parca("7036 sayılı X", "3", "4/9", "Dördüncü bölüm metni.", 0.53),
                _parca("4857 sayılı Y", "17", "", "Başka madde.", 0.50)]
    yanit = mevzuat_yanit.hazirla("soru", parcalar)
    atiflar = [yanit.birincil.atif] + [a.atif for a in yanit.digerleri]
    assert atiflar == ["7036 sayılı X md. 3", "4857 sayılı Y md. 17"]


def test_merged_article_keeps_the_best_score():
    parcalar = [_parca("7036 sayılı X", "3", "5/9", "Beşinci.", 0.53),
                _parca("7036 sayılı X", "3", "1/9", "Birinci.", 0.61)]
    assert mevzuat_yanit.hazirla("soru", parcalar).birincil.puan == 0.61


def test_merged_article_can_highlight_a_sentence_from_any_of_its_pieces():
    parcalar = [_parca("7036 sayılı X", "3", "1/9", "Alakasız bir cümle.", 0.61),
                _parca("7036 sayılı X", "3", "5/9", "Arabulucuya başvurulması dava şartıdır.", 0.53)]
    yanit = mevzuat_yanit.hazirla("arabulucuya başvurmak dava şartı mı", parcalar)
    assert "dava şartıdır" in yanit.birincil.one_cikan


def test_piece_marker_is_stripped_from_the_heading():
    yanit = mevzuat_yanit.hazirla("soru", [_parca("6502 sayılı Z", "45", "2/2", "Metin.", 0.5)])
    assert yanit.birincil.baslik == "Başlık"


# --- tavsiye isteyen sorular -------------------------------------------------

def test_advice_questions_are_refused_without_showing_articles(monkeypatch):
    """Tahmin isteyen soruya madde listesi göstermek, cevabı verdiği izlenimi
    yaratır. Asistan bunun yerine ne yapıp ne yapamayacağını söyler."""
    from app import hukuki_kapsam, mevzuat_yanit as my, retriever

    monkeypatch.setattr(retriever, "get_top_chunks",
                        lambda q, k=None, embed_fn=None, **_: [("6098 sayılı X md. 1 — B\n\nMetin.", 0.9)])
    yanit = my.sor("Bu davayı kazanır mıyım?")
    assert yanit.tavsiye_reddi is True
    assert yanit.birincil is None
    assert yanit.mesaj == hukuki_kapsam.MESAJ


def test_information_questions_still_return_articles(monkeypatch):
    from app import mevzuat_yanit as my, retriever

    monkeypatch.setattr(retriever, "get_top_chunks",
                        lambda q, k=None, embed_fn=None, **_: [("6098 sayılı X md. 344 — B\n\nMetin.", 0.9)])
    yanit = my.sor("Ev sahibi kirayı ne kadar artırabilir?")
    assert yanit.tavsiye_reddi is False
    assert yanit.birincil is not None


def test_displayed_text_and_extracted_sentence_use_the_same_spacing():
    """Vurgulama, çıkarılan cümlenin metinde bulunabilmesine bağlı.

    PDF'ten gelen metin rastgele satır sonları taşıyor; cümle çıkarılırken
    boşluklar sadeleşiyordu. İkisi ayrı biçimde kalınca vurgu hiç eşleşmiyordu.
    """
    ham = ("6502 sayılı X md. 48 — Başlık\n\nMADDE 48- (1) Tüketici, on dört gün\n"
           "içinde   cayma hakkını kullanabilir. (2) İkinci fıkra.")
    yanit = mevzuat_yanit.hazirla("cayma hakkı kaç gün", [(ham, 0.7)])
    assert yanit.birincil.one_cikan in yanit.birincil.metin
    assert "\n" not in yanit.birincil.metin


def test_query_is_expanded_with_statutory_terms_before_retrieval(monkeypatch):
    """Erişime giden sorgu genişletilir; kullanıcıya gösterilen soru değişmez."""
    from app import mevzuat_yanit as my, retriever

    gonderilen = []
    monkeypatch.setattr(retriever, "get_top_chunks",
                        lambda q, k=None, embed_fn=None, **_: gonderilen.append(q) or [])
    my.sor("Tahliye taahhüdü verdim")
    assert "boşaltma" in gonderilen[0].lower()
    assert "Tahliye taahhüdü verdim" in gonderilen[0]


def test_extracted_sentence_is_matched_against_the_original_question(monkeypatch):
    """Öne çıkan cümle özgün soruya göre seçilir; genişletme terimleri
    cümle seçimini kendi kelimeleriyle saptırmamalı."""
    from app import mevzuat_yanit as my, retriever

    parca = ("6098 sayılı X md. 352 — Başlık\n\nMADDE 352 - Kiracı boşaltmayı üstlenmişse "
             "kiraya veren sözleşmeyi sona erdirebilir. Ayrıca kira bedeli ödenmezse.")
    monkeypatch.setattr(retriever, "get_top_chunks", lambda q, k=None, embed_fn=None, **_: [(parca, 0.6)])
    yanit = my.sor("Tahliye taahhüdü verdim, ev sahibi ne yapabilir")
    assert "boşaltmayı üstlenmişse" in yanit.birincil.one_cikan
