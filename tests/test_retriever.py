import pytest

import app.config as config
from app import retriever, store


def test_returns_most_similar_above_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    store.add_chunk("d", "köpekler", [0.0, 1.0])
    res = retriever.get_top_chunks("q", k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert res[0][1] == "kediler"
    # Skor üç sinyalin harmanı: 0.5 kosinüs + 0.3 BM25 + 0.2 bulanık eşleşme.
    # "q" tek harf; ne BM25 ne bulanık katman katkı verir, geriye kosinüs kalır.
    assert res[0][2] == pytest.approx(retriever.YOGUN_AGIRLIK, abs=1e-6)


def test_threshold_filters_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.99)
    store.init_db()
    store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    res = retriever.get_top_chunks("q", embed_fn=lambda t: [[0.0, 1.0]])
    assert res == []


def test_lexical_layer_rescues_a_misspelled_query(tmp_path, monkeypatch):
    """Embedding aynı skoru verse bile bozuk yazımlı sorgu doğru parçayı bulmalı."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    # git parçası embedding'de kasten daha yakın; yalnızca sözlüksel katman bunu çevirebilir.
    store.add_chunk("macos.md", "Ekran görüntüsü belirli bölge: Cmd + Shift + 4", [1.0, 0.1])
    store.add_chunk("git.md", "Son commit'i geri almak için git reset --soft", [1.0, 0.0])

    res = retriever.get_top_chunks(
        "ekran görünütsünü belirli bölgden nasıl alrım",
        k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert res[0][0] == "macos.md"


def test_scores_stay_within_unit_range(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    store.add_chunk("d", "ekran görüntüsü", [1.0, 0.0])
    res = retriever.get_top_chunks("ekran görüntüsü", k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert 0.0 <= res[0][2] <= 1.0


# --- ölçek: sözlüksel katman aday havuzuna uygulanır -------------------------

def test_lexical_scoring_runs_only_on_the_dense_shortlist(monkeypatch):
    """Sözlüksel eşleşme her parçada değil, kosinüsün getirdiği adaylarda çalışır.

    3.069 parçalık mevzuat bilgi tabanında her parçaya SequenceMatcher
    uygulamak sorgu başına 8,7 saniye sürüyordu; kosinüs aynı işi 0,08 saniyede
    yapıyor. Sözlüksel katman yazım hatası toleransı için gerekli, ama yalnız
    en yakın adaylarda gerekli.
    """
    from app import lexical, retriever, store

    parcalar = [(f"k{i}.md", f"parça metni {i}", [1.0 if i == 0 else 0.01, 0.0])
                for i in range(200)]
    monkeypatch.setattr(store, "all_chunks", lambda: parcalar)

    cagrilar = []
    gercek = lexical.fuzzy_score
    monkeypatch.setattr(lexical, "fuzzy_score",
                        lambda q, t: (cagrilar.append(t), gercek(q, t))[1])

    retriever.get_top_chunks("parça metni 0", embed_fn=lambda m: [[1.0, 0.0]])
    assert len(cagrilar) <= retriever.ADAY_HAVUZU
    assert len(cagrilar) < len(parcalar)


def test_shortlist_still_returns_the_best_chunk(monkeypatch):
    from app import retriever, store

    parcalar = [("dogru.md", "aranan metin", [1.0, 0.0])] + \
               [(f"k{i}.md", f"alakasız {i}", [0.0, 1.0]) for i in range(300)]
    monkeypatch.setattr(store, "all_chunks", lambda: parcalar)
    sonuc = retriever.get_top_chunks("aranan metin", embed_fn=lambda m: [[1.0, 0.0]])
    assert sonuc and sonuc[0][0] == "dogru.md"


# --- kelime katmanı bütün korpusu görüyor ------------------------------------

def test_word_layer_improves_the_rank_of_a_chunk_cosine_underrates(monkeypatch):
    """BM25 katmanı aday sıralamasını düzeltir.

    Önceki tasarımda sözlüksel eşleşme yalnız kosinüsün getirdiği adaylarda
    çalışıyordu; kosinüs doğru maddeyi geriye ittiğinde kelime katmanı onu hiç
    göremiyordu. Kanunda ayırt edici terim ("tahliye taahhüdü") birebir geçtiği
    için bu katmanın bütün korpusu görmesi gerekiyor.

    Sav sıralamayla ilgilidir, kabul eşiğiyle değil: eşik korpus istatistiğine
    bağlıdır ve yapay bir örnekte anlamlı değildir.
    """
    from app import bm25, retriever, store
    from app.similarity import cosine

    dogru = ("6098 sayılı TBK", "md. 352 — Kiracı yazılı tahliye taahhüdünde bulunmuşsa "
                                "icra yoluyla tahliye istenebilir.", [0.3, 0.95])
    # Çeldiriciler soruya orta yakınlıkta (kosinüs 0,5): kanun metninde her şey
    # birbirine benzer. Doğru parça anlamsal olarak daha uzak (0,3) ama ayırt
    # edici terimi birebir taşıyor.
    parcalar = [(f"k{i}.md", f"kira sözleşmesi genel hükümleri {i}", [0.5, 0.866])
                for i in range(200)] + [dogru]
    monkeypatch.setattr(store, "all_chunks", lambda: parcalar)
    monkeypatch.setattr(retriever, "_dizin_onbellek", None)

    sorgu = "tahliye taahhüdü verdim ne olur"
    qvec = [1.0, 0.0]
    metinler = [t for (_s, t, _e) in parcalar]
    kelime = bm25.Dizin(metinler).normalize(sorgu)

    def sira(anahtar):
        return sorted(range(len(parcalar)), key=anahtar, reverse=True).index(len(parcalar) - 1)

    yalniz_kosinus = sira(lambda i: cosine(qvec, parcalar[i][2]))
    harman = sira(lambda i: retriever.YOGUN_AGIRLIK * cosine(qvec, parcalar[i][2])
                  + retriever.KELIME_AGIRLIK * kelime.get(i, 0.0))
    assert harman < yalniz_kosinus, "kelime katmanı doğru parçayı yukarı taşımalı"
    assert harman == 0, "ayırt edici terimi taşıyan tek parça başa gelmeli"


def test_index_is_rebuilt_when_the_knowledge_base_changes(monkeypatch):
    from app import retriever, store

    monkeypatch.setattr(retriever, "_dizin_onbellek", None)
    monkeypatch.setattr(store, "all_chunks", lambda: [("a.md", "birinci metin", [1.0])])
    retriever.get_top_chunks("birinci", embed_fn=lambda m: [[1.0]])
    ilk = retriever._dizin_onbellek

    monkeypatch.setattr(store, "all_chunks",
                        lambda: [("a.md", "birinci metin", [1.0]), ("b.md", "ikinci", [1.0])])
    retriever.get_top_chunks("ikinci", embed_fn=lambda m: [[1.0]])
    assert retriever._dizin_onbellek is not ilk


# --- madde başlığı ayrı bir sinyal -------------------------------------------

def test_heading_match_lifts_an_article_whose_title_answers_the_question(monkeypatch):
    """Kanun maddelerinin başlığı, kanun koyucunun yazdığı konu etiketidir.

    "Dava şartları nelerdir?" sorusunun cevabı başlığı tam da "Dava şartları"
    olan maddedir; ama başlık 600 karakterlik gövdenin içinde üç kelimedir ve
    sinyali erir. Başlık eşleşmesine ayrı bir puan verilir.
    """
    from app import retriever, store

    dogru = ("6100 sayılı HMK", "6100 sayılı HMK md. 114 — Dava şartları\n\nMADDE 114- Hüküm.",
             [0.5, 0.866])
    rakip = ("6100 sayılı HMK", "6100 sayılı HMK md. 132 — Karşı dava açılabilmesinin şartları"
                                "\n\nMADDE 132- Uzun bir hüküm metni burada.", [0.55, 0.835])
    monkeypatch.setattr(store, "all_chunks", lambda: [rakip, dogru])
    monkeypatch.setattr(retriever, "_dizin_onbellek", None)
    sonuc = retriever.get_top_chunks("Dava şartları nelerdir?",
                                     embed_fn=lambda m: [[1.0, 0.0]], k=2)
    assert "md. 114" in sonuc[0][1]


def test_heading_score_uses_the_original_question_not_the_expanded_one(monkeypatch):
    """Sorgu kanun terimleriyle genişletiliyor; başlık puanı özgün soruya bakmalı.

    Genişletilmiş sorguda daha çok kelime vardır ve her başlık daha kolay
    eşleşir — sinyal körelir.
    """
    from app import lexical, retriever, store

    gorulen = []
    gercek = lexical.fuzzy_score
    monkeypatch.setattr(lexical, "fuzzy_score",
                        lambda a, b: (gorulen.append(b), gercek(a, b))[1])
    # Başlık en az iki anlamlı kelime taşımalı, yoksa puan hesaplanmaz.
    monkeypatch.setattr(store, "all_chunks",
                        lambda: [("k.md", "k.md md. 1 — Dava şartları\n\nMetin.", [1.0, 0.0])])
    monkeypatch.setattr(retriever, "_dizin_onbellek", None)
    retriever.get_top_chunks("genişletilmiş sorgu ek terim", embed_fn=lambda m: [[1.0, 0.0]],
                             baslik_sorgusu="özgün soru")
    assert "özgün soru" in gorulen


def test_chunk_without_a_heading_is_not_penalised(monkeypatch):
    from app import retriever, store

    monkeypatch.setattr(store, "all_chunks",
                        lambda: [("k.md", "k.md md. 5\n\nBaşlıksız madde metni.", [1.0, 0.0])])
    monkeypatch.setattr(retriever, "_dizin_onbellek", None)
    assert retriever.get_top_chunks("başlıksız madde", embed_fn=lambda m: [[1.0, 0.0]])


def test_single_word_generic_heading_earns_no_bonus(monkeypatch):
    """Tek kelimelik başlık bilgi taşımaz ve yanlış eşleşme üretir.

    Bu gerçekten oldu: "Grip aşısı ne zaman yaptırılır?" sorusu, başlığı
    "2. Zamanı" olan bir Medeni Kanun maddesini çekti ve asistanın hukuk dışı
    soruyu reddetme yetisi bozuldu. Başlık ancak birden çok anlamlı kelime
    taşıyorsa puan alır.
    """
    from app import retriever

    assert retriever.baslik_puani("2. Zamanı", "Grip aşısı ne zaman yaptırılır?") == 0.0
    assert retriever.baslik_puani("Dava şartları", "Dava şartları nelerdir?") > 0.5
