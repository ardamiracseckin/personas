"""Değerlendirme koşumu sadakati ölçüyor ve rapora yazıyor mu.

Kalite puanı "doğru bilgi cevapta var mı" der; sadakat "cevap getirilen parçaya
mı dayanıyor" der. Rapor ikisini ayrı göstermeli, yoksa modelin ezberden verdiği
doğru cevap RAG zinciri çalışıyormuş gibi görünür.
"""
from scripts import evaluate

BAGLAM = [{"source": "git.md", "text": "Yarım kalan değişiklikleri saklamak için `git stash` "
                                       "çalıştırılır, geri getirmek için `git stash pop`.",
           "score": 0.7}]


def _row(rid, text, grounding, category="cevaplanabilir"):
    return {"id": rid, "category": category, "question": "soru", "expected_source": "git.md",
            "text": text, "score": 2, "sources": ["git.md"], "chunks": BAGLAM, "seconds": 1.0,
            "error": None, "abstained": False, "abstained_by": None, "grounding": grounding}


def test_answers_without_chunks_are_not_measured():
    # Takvim/mail cevaplarında getirilen parça yoktur; sadakat ölçümü onlara uygulanmaz.
    assert evaluate.measure_grounding("Bugün iki etkinliğin var.", [], "bugün ne var") is None


def test_answer_grounded_in_the_retrieved_chunk_scores_high():
    cevap = "Değişiklikleri saklamak için `git stash`, geri getirmek için `git stash pop`."
    assert evaluate.measure_grounding(cevap, BAGLAM, "nasıl saklarım") > 0.8


def test_summary_ignores_unmeasured_rows():
    ozet = evaluate.faithfulness_summary([_row("s1", "a", 1.0), _row("s2", "b", 0.5),
                                          _row("s3", "c", None)])
    assert ozet["olculen"] == 2
    assert ozet["ortalama"] == 0.75


def test_summary_flags_answers_below_the_threshold():
    ozet = evaluate.faithfulness_summary([_row("s1", "a", 0.95),
                                          _row("s2", "uydurma", 0.30)])
    assert [r["id"] for r in ozet["dusuk"]] == ["s2"]


def test_summary_is_empty_when_nothing_is_measurable():
    ozet = evaluate.faithfulness_summary([_row("s1", "a", None)])
    assert ozet["olculen"] == 0
    assert ozet["ortalama"] is None


def test_report_shows_faithfulness_next_to_quality():
    meta = {"timestamp": "01.01.2026 00:00", "model_id": "phi-4-mini", "k": 3,
            "threshold": 0.34, "chunks": 58, "sources": 9}
    rapor = evaluate.build_report(meta, [], [], [], [], [],
                                  [_row("s1", "a", 1.0), _row("s2", "b", 0.4)], [])
    assert "Sadakat" in rapor
    assert "%70" in rapor  # (1.0 + 0.4) / 2


def test_low_grounding_rows_name_the_unsupported_words():
    # Rapor sadece "düşük" demekle kalmamalı; hangi kelimenin bağlamda karşılığı
    # olmadığını göstermeli, yoksa bulgu incelenebilir olmaz.
    meta = {"timestamp": "01.01.2026 00:00", "model_id": "phi-4-mini", "k": 3,
            "threshold": 0.34, "chunks": 58, "sources": 9}
    uydurma = _row("s1", "Docker konteynerini yeniden başlat.", 0.2)
    rapor = evaluate.build_report(meta, [], [], [], [], [], [uydurma], [])
    assert "docker" in rapor


def test_answer_rows_carry_the_retrieved_chunks_and_their_grounding():
    # Elle inceleme ve rapor tablosu için parçalar satırda durmalı.
    soru = {"id": "s1", "category": "cevaplanabilir", "question": "nasıl saklarım",
            "expected_source": "git.md", "expected_substrings": ["git stash"]}
    res = {"text": "Saklamak için `git stash` çalıştırılır.", "sources": ["git.md"],
           "chunks": BAGLAM, "pending_action": None}
    satir = evaluate.answer_row(soru, res, elapsed=1.5, error=None)
    assert satir["chunks"] == BAGLAM
    assert satir["grounding"] > 0.8
    assert satir["score"] == 2


# --- kod sadakati -------------------------------------------------------------

META = {"timestamp": "01.01.2026 00:00", "model_id": "phi-4-mini", "k": 3,
        "threshold": 0.34, "chunks": 58, "sources": 9}


def test_answer_rows_list_commands_missing_from_the_context():
    soru = {"id": "s1", "category": "cevaplanabilir", "question": "nasıl saklarım",
            "expected_source": "git.md", "expected_substrings": None}
    res = {"text": "Bunun için `docker stash` çalıştır.", "sources": ["git.md"],
           "chunks": BAGLAM, "pending_action": None}
    assert evaluate.answer_row(soru, res, 1.0, None)["invented_code"] == ["docker stash"]


def test_report_names_the_invented_command():
    satir = _row("s1", "Bunun için `docker stash` çalıştır.", 0.4)
    satir["invented_code"] = ["docker stash"]
    rapor = evaluate.build_report(META, [], [], [], [], [], [satir], [])
    assert "Kod sadakati" in rapor
    assert "docker stash" in rapor


def test_report_reports_clean_code_faithfulness_when_nothing_is_invented():
    satir = _row("s1", "Bunun için `git stash` çalıştır.", 0.9)
    satir["invented_code"] = []
    rapor = evaluate.build_report(META, [], [], [], [], [], [satir], [])
    assert "Kod sadakati | 1/1" in rapor


# --- eşik taraması ------------------------------------------------------------
#
# İki eşik de tahminle değil ölçümle seçilmeli: SIM_THRESHOLD ve TOP_K taramayla
# seçilmişti, raporun tamamı bunun üzerine kurulu.

def _kategorili(rid, kategori, dayanak):
    satir = _row(rid, "metin", dayanak, category=kategori)
    return satir


def test_floor_sweep_separates_document_answers_from_improvised_ones():
    cevaplar = [_kategorili("C1", "cevaplanabilir", 0.9),
                _kategorili("C2", "cevaplanabilir", 0.7),
                _kategorili("U1", "uc_durum", 0.2),
                _kategorili("U2", "uc_durum", 0.6)]
    tarama = {r["floor"]: r for r in evaluate.grounding_floor_sweep(cevaplar, [0.5, 0.65, 0.8])}
    # 0.65: belge cevaplarının ikisi de üstte kalır, uç durumların ikisi de yakalanır
    assert tarama[0.65]["yanlis_alarm"] == 0
    assert tarama[0.65]["yakalanan"] == 2
    # 0.8: artık doğru bir belge cevabı da düşük işaretlenir
    assert tarama[0.8]["yanlis_alarm"] == 1


def test_citation_sweep_reports_coverage_and_off_source_rate():
    baglam = [{"source": "git.md", "score": 0.6,
               "text": "Değişiklikleri saklamak için `git stash` çalıştırılır."},
              {"source": "docker.md", "score": 0.4,
               "text": "Konteyner listesi için `docker ps` çalıştırılır."}]
    satir = _row("C1", "Değişiklikleri saklamak için `git stash` çalıştırılır.", 1.0)
    satir["chunks"] = baglam
    tarama = {r["threshold"]: r for r in
              evaluate.citation_threshold_sweep([satir], [0.4, 0.9])}
    assert tarama[0.4]["kapsanan"] == 1
    assert tarama[0.4]["beklenen_disi"] == 0
    assert tarama[0.9]["kapsanan"] == 1


def test_citation_sweep_counts_attributions_to_the_wrong_document():
    baglam = [{"source": "docker.md", "score": 0.6,
               "text": "Konteyner listesi için `docker ps` çalıştırılır."}]
    satir = _row("C1", "Konteyner listesi için `docker ps` çalıştırılır.", 1.0)
    satir["chunks"] = baglam  # beklenen kaynak git.md, atıf docker.md'ye gidiyor
    tarama = evaluate.citation_threshold_sweep([satir], [0.5])[0]
    assert tarama["beklenen_disi"] == 1


def test_sweep_report_shows_both_tables_and_the_chosen_values():
    rapor = evaluate.build_sweep_report(
        {"timestamp": "01.01.2026 00:00", "model_id": "phi-4-mini", "kaynak": "x.json"},
        [{"floor": 0.6, "yanlis_alarm": 0, "beklenen": 13, "yakalanan": 2, "ucdurum": 3}],
        [{"threshold": 0.55, "cumle": 20, "kapsanan": 18, "beklenen_disi": 1}])
    assert "Sadakat eşiği" in rapor and "Atıf eşiği" in rapor
    assert "0.60" in rapor and "0.55" in rapor


def test_citation_sweep_also_counts_attributions_on_improvised_answers():
    # Uç durum cevaplarında model belgeye değil kendi bilgisine dayanır; iyi bir
    # eşik oralarda atıf vermemeli. Asıl denge bu: kapsama ↑ ile doğaçlamaya atıf ↓.
    baglam = [{"source": "git.md", "score": 0.4,
               "text": "Değişiklikleri saklamak için `git stash` çalıştırılır."}]
    # Cümlenin bağlamla kısmi örtüşmesi var (1/5): düşük eşikte atıf alır, yüksekte almaz.
    dogaclama = _row("U1", "Değişiklikleri öğrenmek için sırayı takip edin.", 0.3,
                     category="uc_durum")
    dogaclama["chunks"] = baglam
    tarama = {r["threshold"]: r for r in
              evaluate.citation_threshold_sweep([dogaclama], [0.1, 0.9])}
    assert tarama[0.1]["dogaclamaya_atif"] == 1
    assert tarama[0.9]["dogaclamaya_atif"] == 0
