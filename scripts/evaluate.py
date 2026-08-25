"""Değerlendirme koşumu: soru setini çalıştırır, metrikleri hesaplar, rapor yazar.

Deterministik metrikler (yönlendirme doğruluğu, erişim isabeti) sohbet modeli
gerektirmez; yalnızca yerel embedding kullanır ve saniyeler sürer. Üretim
metrikleri (cevap, çekimserlik, gecikme) Foundry Local'deki sohbet modelini çağırır.

Kullanım:
    python scripts/evaluate.py                       # tam koşum + rapor
    python scripts/evaluate.py --llm-yok             # sadece deterministik metrikler
    python scripts/evaluate.py --esik 0.10,0.15,0.20 # eşik/K taraması (LLM'siz)
    python scripts/evaluate.py --model qwen3-1.7b    # başka sohbet modeliyle koş
"""
import argparse
import json
import os
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import (assistant, citations, config, grounding, lexical, llm, retriever,  # noqa: E402
                 router, store)
from app.similarity import cosine  # noqa: E402

QUESTIONS_PATH = ROOT / "eval" / "questions.json"
OUT_DIR = ROOT / "docs" / "eval"
ANSWER_CATEGORIES = ("cevaplanabilir", "cevaplanamaz", "uc_durum")
# Bu oranın altındaki cevap, getirilen parçanın dışına çıkmış sayılır ve raporda ayrı listelenir.
GROUNDING_FLOOR = 0.60

# Çekimserlik iki katmanda oluşabilir: erişim eşiği hiç parça bırakmazsa asistan
# sabit NO_INFO metnini döndürür; parça geldiği hâlde bağlam yetersizse modelin
# kendisi istemdeki kural gereği bilmediğini söyler. İkincisi serbest metindir.
ABSTAIN_RE = re.compile(r"bilgi(m)? yok|bilmiyorum|bulamadım", re.IGNORECASE)


def is_abstention(text):
    return bool(ABSTAIN_RE.search(text or ""))


def _normalize(text):
    """Karşılaştırma için boşlukları at: 'Cmd + Shift + 4' ile 'Cmd+Shift+4' aynı sayılsın."""
    return "".join((text or "").lower().split())


def quality_score(answer_text, expected_substrings):
    """Beklenen ifadelere göre 0-2 puan. Elle puanlamanın tekrarlanabilir yaklaşığı."""
    if not expected_substrings:
        return None
    metin = _normalize(answer_text)
    tutan = sum(1 for parca in expected_substrings if _normalize(parca) in metin)
    if tutan == len(expected_substrings):
        return 2
    return 1 if tutan else 0


def measure_grounding(answer_text, chunks, question):
    """Cevabın getirilen parçalara dayanma oranı; ölçülemiyorsa None.

    Takvim/mail gibi belge dışı akışlarda getirilen parça yoktur — oraya sadakat
    ölçütü uygulanamaz, 0 yazmak da yanıltıcı olur.
    """
    if not chunks:
        return None
    return grounding.score(answer_text, [c["text"] for c in chunks], question)


def faithfulness_summary(answers):
    """Ölçülebilen cevaplar üzerinden ortalama sadakat + eşiğin altında kalanlar."""
    olculen = [a for a in answers if a.get("grounding") is not None]
    return {
        "olculen": len(olculen),
        "ortalama": (sum(a["grounding"] for a in olculen) / len(olculen)) if olculen else None,
        "dusuk": [a for a in olculen if a["grounding"] < GROUNDING_FLOOR],
    }


def grounding_floor_sweep(answers, floors):
    """Sadakat eşiğini ölçümle seçmek için: her eşikte yanlış alarm / yakalanan.

    Ayrım şu iki grup üzerinden yapılır: `cevaplanabilir` sorular belgeye dayanmak
    zorundadır (eşiğin altına düşerlerse yanlış alarm), `uc_durum` cevaplarında ise
    model belgeye değil kendi bilgisine dayanıp genel tavsiye verir (yakalanmalı).
    """
    beklenen = [a for a in answers
                if a["category"] == "cevaplanabilir" and a.get("grounding") is not None]
    ucdurum = [a for a in answers
               if a["category"] == "uc_durum" and a.get("grounding") is not None]
    return [{"floor": esik,
             "yanlis_alarm": sum(1 for a in beklenen if a["grounding"] < esik),
             "beklenen": len(beklenen),
             "yakalanan": sum(1 for a in ucdurum if a["grounding"] < esik),
             "ucdurum": len(ucdurum)}
            for esik in floors]


def citation_threshold_sweep(answers, thresholds):
    """Atıf eşiğini ölçümle seçmek için: kapsama ve beklenen kaynak dışına atıf.

    Asıl denge `dogaclamaya_atif` sütununda: uç durum cevaplarında model belgeye
    değil kendi bilgisine dayanır, oralarda atıf verilmemelidir. Yanlış atıf,
    atıfsızlıktan kötüdür.

    `beklenen_disi` ise vekil bir ölçüttür, kesin hata değil: bir cevap gerçekten
    ikinci bir belgeden de beslenebilir (C06 hem python hem vscode notlarını
    kullanıyor).
    """
    kaynakli = [a for a in answers
                if a["category"] == "cevaplanabilir" and a.get("chunks")
                and a.get("expected_source")]
    dogaclama = [a for a in answers if a["category"] == "uc_durum" and a.get("chunks")]
    rows = []
    for esik in thresholds:
        cumle = kapsanan = disari = 0
        for a in kaynakli:
            cumle += len(citations.spans(a["text"]))
            for atif in citations.attribute(a["text"], a["chunks"], threshold=esik):
                kapsanan += 1
                disari += atif["source"] != a["expected_source"]
        uc_cumle = sum(len(citations.spans(a["text"])) for a in dogaclama)
        uc_atif = sum(len(citations.attribute(a["text"], a["chunks"], threshold=esik))
                      for a in dogaclama)
        rows.append({"threshold": esik, "cumle": cumle, "kapsanan": kapsanan,
                     "beklenen_disi": disari, "uc_cumle": uc_cumle,
                     "dogaclamaya_atif": uc_atif})
    return rows


def code_faithfulness(answers):
    """Kod sadakati: bağlamda bulunmayan komut üreten cevaplar.

    Sözlüksel oran bulanıktır; komut uydurmak ikili bir hatadır ve kullanıcının
    çalıştıracağı yanlış komut demektir. Bu yüzden ayrı sayılır.
    """
    kodlu = [a for a in answers if a.get("chunks") and grounding.code_spans(a["text"])]
    return {"kodlu": len(kodlu),
            "uyduran": [a for a in kodlu if a.get("invented_code")]}


def load_questions():
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return data["questions"]


def by_category(questions, name):
    return [q for q in questions if q["category"] == name]


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, int(round(p * (len(ordered) - 1))))
    return ordered[idx]


# ---------------------------------------------------------------- deterministik

def score_questions(questions):
    """Her soru için (kaynak, skor) sıralı listesi. Tek embedding turu, LLM yok.

    Skor, uygulamanın kullandığı `retriever.score` ile birebir aynıdır (kosinüs +
    sözlüksel). Burada kosinüsü tek başına hesaplamak, ölçümün uygulamadan
    sapmasına yol açıyordu.
    """
    chunks = store.all_chunks()
    if not chunks:
        raise SystemExit("Veritabanı boş. Önce 'python -m app.ingest' çalıştırın.")
    texts = [q["question"] for q in questions]
    vectors = llm.embed(texts)
    scored = {}
    for q, qvec in zip(questions, vectors):
        rows = []
        for (src, text, emb) in chunks:
            dense = cosine(qvec, emb)
            lex = lexical.fuzzy_score(q["question"], text)
            rows.append((src, config.DENSE_WEIGHT * dense + config.LEXICAL_WEIGHT * lex,
                         dense, lex))
        rows.sort(key=lambda r: r[1], reverse=True)
        scored[q["id"]] = rows
    return scored


def _accepted(rows, k, threshold):
    """Uygulamanın kabul kuralıyla aynı: eşik veya güçlü kelime eşleşmesi."""
    return [(src, total) for (src, total, dense, lex) in rows
            if retriever.accepts(total, dense, lex, threshold)][:k]


def run_routing(questions):
    rows = []
    for q in by_category(questions, "yonlendirme"):
        got = router.route(q["question"])
        rows.append({
            "id": q["id"], "question": q["question"],
            "expected": q["expected_route"], "got": got,
            "ok": got == q["expected_route"],
        })
    return rows


def _hits(questions, scored, k, threshold, category):
    satirlar = []
    for q in by_category(questions, category):
        top = _accepted(scored[q["id"]], k, threshold)
        satirlar.append({
            "id": q["id"], "question": q["question"],
            "expected": q["expected_source"],
            "got": [s for (s, _sc) in top],
            "best_score": scored[q["id"]][0][1],
            "ok": any(s == q["expected_source"] for (s, _sc) in top),
        })
    return satirlar


def run_retrieval(questions, scored, k, threshold):
    """Erişim isabeti (temiz ve yazım hatalı sorular) + cevaplanamazda çekimserlik."""
    hits = _hits(questions, scored, k, threshold, "cevaplanabilir")
    typo = _hits(questions, scored, k, threshold, "yazim_hatasi")
    kisa = _hits(questions, scored, k, threshold, "kisa_sorgu")
    abstains = []
    for q in by_category(questions, "cevaplanamaz"):
        top = _accepted(scored[q["id"]], k, threshold)
        abstains.append({
            "id": q["id"], "question": q["question"],
            "best_score": scored[q["id"]][0][1],
            "ok": not top,  # eşiği geçen parça yoksa asistan "bilgim yok" der
        })
    return hits, typo, kisa, abstains


def run_sweep(questions, scored, thresholds, ks):
    rows = []
    for k in ks:
        for t in thresholds:
            hits, typo, kisa, abstains = run_retrieval(questions, scored, k, t)
            hit_rate = sum(h["ok"] for h in hits) / len(hits)
            typo_rate = sum(h["ok"] for h in typo) / len(typo) if typo else 0.0
            kisa_rate = sum(h["ok"] for h in kisa) / len(kisa) if kisa else 0.0
            abstain_rate = sum(a["ok"] for a in abstains) / len(abstains)
            rows.append({
                "k": k, "threshold": t, "hit": hit_rate, "typo": typo_rate,
                "kisa": kisa_rate, "abstain": abstain_rate,
                "balance": (hit_rate + typo_rate + kisa_rate + abstain_rate) / 4,
            })
    return rows


# --------------------------------------------------------------------- üretim

def apply_model(alias):
    """Sohbet modelini değiştir ve gerçekten onun yüklendiğini doğrula."""
    config.CHAT_MODEL = alias
    _client, model_id = llm._client()
    if not model_id.lower().startswith(alias.lower()):
        raise SystemExit(
            f"'{alias}' Foundry Local'de yüklü değil (servis '{model_id}' döndürdü).\n"
            f"Önce çalıştırın: foundry model load {alias}"
        )
    return model_id


def answer_row(question, res, elapsed, error):
    """Bir sorunun rapor satırı. `res`: assistant.answer() sonucu (hata varsa boş)."""
    text, parcalar = res["text"], res["chunks"]
    return {
        "id": question["id"], "category": question["category"],
        "question": question["question"], "expected_source": question.get("expected_source"),
        "text": text, "score": quality_score(text, question.get("expected_substrings")),
        "sources": res["sources"], "chunks": parcalar, "seconds": elapsed, "error": error,
        "grounding": measure_grounding(text, parcalar, question["question"]),
        "invented_code": grounding.unsupported_code_spans(
            text, [c["text"] for c in parcalar]),
        "abstained": is_abstention(text),
        "abstained_by": ("erişim" if text.strip() == assistant.NO_INFO
                         else "model" if is_abstention(text) else None),
    }


def run_answers(questions, categories):
    print("  ısınma turu…", flush=True)
    try:
        llm.chat("Kısa cevap ver.", "merhaba")
    except Exception as e:
        raise SystemExit(f"Sohbet modeline ulaşılamadı: {e}")
    rows = []
    for q in questions:
        if q["category"] not in categories:
            continue
        started = time.perf_counter()
        try:
            res, error = assistant.answer(q["question"]), None
        except Exception as e:  # uç durumlar çökmemeli; çökerse rapora yazılır
            res = {"text": "", "sources": [], "chunks": []}
            error = f"{type(e).__name__}: {e}"
        elapsed = time.perf_counter() - started
        rows.append(answer_row(q, res, elapsed, error))
        text = rows[-1]["text"]
        flag = "!" if error else ("~" if is_abstention(text) else "+")
        puan, dayanak = rows[-1]["score"], rows[-1]["grounding"]
        etiket = "" if puan is None else f" puan={puan}"
        etiket += "" if dayanak is None else f" dayanak={dayanak:.2f}"
        print(f"  [{flag}] {q['id']} {elapsed:5.2f}s{etiket}  {q['question'][:44]}", flush=True)
    return rows


# ---------------------------------------------------------------------- rapor

def _table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build_report(meta, routing, hits, typo, kisa, abstains, answers, sweep):
    ok = lambda flag: "✅" if flag else "❌"  # noqa: E731
    lines = [
        f"# Değerlendirme sonuçları — {meta['timestamp']}",
        "",
        _table(["Ayar", "Değer"], [
            ["Sohbet modeli", f"`{meta['model_id']}`"],
            ["Embedding modeli", f"`{config.EMBED_MODEL}`"],
            ["TOP_K", meta["k"]],
            ["SIM_THRESHOLD", meta["threshold"]],
            ["Bilgi tabanı", f"{meta['chunks']} parça / {meta['sources']} belge"],
        ]),
        "",
    ]

    if routing:
        acc = sum(r["ok"] for r in routing) / len(routing)
        lines += [f"## Yönlendirme doğruluğu — {acc:.0%} ({sum(r['ok'] for r in routing)}/{len(routing)})",
                  "", _table(["ID", "Soru", "Beklenen", "Gelen", "Sonuç"], [
                      [r["id"], r["question"][:48],
                       f"{r['expected']['tool']}/{r['expected']['action']}",
                       f"{r['got']['tool']}/{r['got']['action']}", ok(r["ok"])]
                      for r in routing]), ""]

    if hits:
        rate = sum(h["ok"] for h in hits) / len(hits)
        lines += [f"## Erişim isabeti (hit@{meta['k']}) — {rate:.0%} ({sum(h['ok'] for h in hits)}/{len(hits)})",
                  "", _table(["ID", "Soru", "Beklenen kaynak", "Getirilen", "En yüksek skor", "Sonuç"], [
                      [h["id"], h["question"][:44], h["expected"],
                       ", ".join(dict.fromkeys(h["got"])) or "—",
                       f"{h['best_score']:.3f}", ok(h["ok"])]
                      for h in hits]), ""]

    if typo:
        rate = sum(h["ok"] for h in typo) / len(typo)
        lines += [f"## Yazım hatalı sorularda erişim — {rate:.0%} ({sum(h['ok'] for h in typo)}/{len(typo)})",
                  "", _table(["ID", "Bozuk yazımlı soru", "Beklenen kaynak", "En yüksek skor", "Sonuç"], [
                      [h["id"], h["question"][:46], h["expected"],
                       f"{h['best_score']:.3f}", ok(h["ok"])]
                      for h in typo]), ""]

    if kisa:
        rate = sum(h["ok"] for h in kisa) / len(kisa)
        lines += [f"## Kısa sorgularda erişim — {rate:.0%} ({sum(h['ok'] for h in kisa)}/{len(kisa)})",
                  "", _table(["ID", "Sorgu", "Beklenen kaynak", "En yüksek skor", "Sonuç"], [
                      [h["id"], h["question"][:40], h["expected"],
                       f"{h['best_score']:.3f}", ok(h["ok"])] for h in kisa]), ""]

    if abstains:
        rate = sum(a["ok"] for a in abstains) / len(abstains)
        lines += [f"## Çekimserlik (cevaplanamaz sorular) — {rate:.0%} ({sum(a['ok'] for a in abstains)}/{len(abstains)})",
                  "", _table(["ID", "Soru", "En yüksek skor", "Eşiğin altında mı"], [
                      [a["id"], a["question"][:48], f"{a['best_score']:.3f}", ok(a["ok"])]
                      for a in abstains]), ""]

    if sweep:
        best = max(sweep, key=lambda r: (r["balance"], -r["threshold"]))
        lines += ["## Eşik / K taraması", "",
                  _table(["K", "Eşik", "İsabet", "Yazım hatalı", "Kısa sorgu", "Çekimserlik",
                          "Denge"], [
                      [r["k"], f"{r['threshold']:.2f}", f"{r['hit']:.0%}", f"{r['typo']:.0%}",
                       f"{r['kisa']:.0%}", f"{r['abstain']:.0%}", f"{r['balance']:.0%}"]
                      for r in sweep]),
                  "", f"En iyi denge: **K={best['k']}, eşik={best['threshold']:.2f}** "
                      f"(isabet {best['hit']:.0%}, yazım hatalı {best['typo']:.0%}, "
                      f"kısa {best['kisa']:.0%}, çekimserlik {best['abstain']:.0%})", ""]

    if answers:
        times = [a["seconds"] for a in answers]
        errors = [a for a in answers if a["error"]]
        unans = [a for a in answers if a["category"] == "cevaplanamaz"]
        puanlar = [a["score"] for a in answers if a.get("score") is not None]
        sadakat = faithfulness_summary(answers)
        kod = code_faithfulness(answers)
        abst = sum(a["abstained"] for a in unans)
        by_model = sum(a["abstained_by"] == "model" for a in unans)
        lines += ["## Üretim (uçtan uca cevaplar)", "",
                  _table(["Metrik", "Değer"], [
                      ["Soru sayısı", len(answers)],
                      ["Ortalama süre", f"{statistics.mean(times):.2f} sn"],
                      ["p50 süre", f"{percentile(times, 0.50):.2f} sn"],
                      ["p95 süre", f"{percentile(times, 0.95):.2f} sn"],
                      ["Cevaplanamazda çekimserlik", f"{abst}/{len(unans)}" if unans else "—"],
                      ["  — eşik sayesinde / model sayesinde",
                       f"{abst - by_model} / {by_model}" if unans else "—"],
                      ["Hata / çökme", len(errors)],
                  ] + ([["Otomatik kalite puanı",
                         f"{sum(puanlar)}/{2 * len(puanlar)} (%{100 * sum(puanlar) / (2 * len(puanlar)):.0f})"]]
                       if puanlar else [])
                    + ([["Sadakat (ortalama)",
                         f"%{100 * sadakat['ortalama']:.0f} — {sadakat['olculen']} cevapta ölçüldü"]]
                       if sadakat["olculen"] else [])
                    + ([["Kod sadakati",
                         f"{kod['kodlu'] - len(kod['uyduran'])}/{kod['kodlu']} "
                         f"cevapta uydurulmuş komut yok"]] if kod["kodlu"] else [])), "",
                  "Otomatik puan beklenen ifadelere bakar (2 = hepsi, 1 = bir kısmı, 0 = hiçbiri); "
                  "elle puan sütunu gerekirse insan değerlendirmesi için boş bırakılmıştır.",
                  "", _table(["ID", "Kategori", "Soru", "Cevap", "Kaynaklar", "Süre", "Oto",
                              "Sadakat", "Elle"], [
                      [a["id"], a["category"], a["question"][:40] or "(boş)",
                       (a["error"] or a["text"]).replace("\n", " ")[:110],
                       ", ".join(dict.fromkeys(a["sources"])) or "—",
                       f"{a['seconds']:.2f}",
                       "—" if a.get("score") is None else a["score"],
                       "—" if a.get("grounding") is None else f"{a['grounding']:.2f}", " "]
                      for a in answers]), ""]

        lines += ["### Sadakat (cevap getirilen parçaya mı dayanıyor)", ""]
        if not sadakat["olculen"]:
            lines += ["Belge akışıyla üretilmiş ölçülebilir cevap yok.", ""]
        else:
            lines += [
                "Kalite puanı doğru bilginin cevapta geçip geçmediğine bakar; sadakat ise cevabın "
                "getirilen parçalardan mı yoksa modelin ezberinden mi geldiğini ölçer. Ölçüt "
                "sözlükseldir: cevaptaki içerik kelimelerinin kaçının bağlamda karşılığı var "
                f"(sorudan gelen kelimeler sayılmaz). {GROUNDING_FLOOR:.2f} altı ayrıca listelenir.",
                ""]
            if sadakat["dusuk"]:
                lines += [f"Eşiğin altında kalan {len(sadakat['dusuk'])} cevap:", "",
                          _table(["ID", "Soru", "Sadakat", "Bağlamda karşılığı olmayan kelimeler"], [
                              [a["id"], a["question"][:40] or "(boş)", f"{a['grounding']:.2f}",
                               ", ".join(grounding.unsupported_tokens(
                                   a["text"], [c["text"] for c in a.get("chunks", [])],
                                   a["question"])[:8]) or "—"]
                              for a in sadakat["dusuk"]]), ""]
            else:
                lines += [f"Ölçülen cevapların hepsi {GROUNDING_FLOOR:.2f} eşiğinin üzerinde.", ""]

        if kod["kodlu"]:
            lines += ["### Kod sadakati (uydurulmuş komut var mı)", "",
                      "Ters tırnak içindeki her ifade bağlamda birebir geçmeli. Geçmiyorsa model "
                      "komutu kendisi türetmiştir — kullanıcının çalıştıracağı yanlış komut budur.",
                      ""]
            if kod["uyduran"]:
                lines += [_table(["ID", "Soru", "Bağlamda olmayan komut"], [
                    [a["id"], a["question"][:40] or "(boş)", ", ".join(f"`{c}`" for c in
                                                                      a["invented_code"])]
                    for a in kod["uyduran"]]), ""]
            else:
                lines += [f"Komut içeren {kod['kodlu']} cevabın hepsinde komutlar bağlamdan "
                          f"geliyor; uydurulmuş komut yok.", ""]

    return "\n".join(lines) + "\n"


def build_sweep_report(meta, floor_rows, cite_rows):
    """Sadakat ve atıf eşiklerinin taraması. Kayıtlı bir koşum JSON'undan üretilir."""
    return "\n".join([
        f"# Sadakat ve atıf eşiği taraması — {meta['timestamp']}",
        "",
        f"Kaynak koşum: `{meta['kaynak']}` (model `{meta['model_id']}`). Model çağrılmaz; "
        "kayıtlı cevaplar ve parçalar üzerinden yeniden hesaplanır.",
        "",
        "## Sadakat eşiği (raporda 'düşük' sayılma sınırı)",
        "",
        "`cevaplanabilir` cevaplar belgeye dayanmak zorundadır — eşiğin altına düşerlerse yanlış "
        "alarm. `uc_durum` cevaplarında model belgeye değil kendi bilgisine dayanır — yakalanmalı.",
        "",
        _table(["Eşik", "Yanlış alarm", "Yakalanan"],
               [[f"{r['floor']:.2f}", f"{r['yanlis_alarm']}/{r['beklenen']}",
                 f"{r['yakalanan']}/{r['ucdurum']}"] for r in floor_rows]),
        "",
        "## Atıf eşiği (cümleye atıf verme sınırı)",
        "",
        "Asıl denge ortadaki sütunda: `cevaplanabilir` cevaplarda kapsama yüksek olmalı, "
        "`uc_durum` cevaplarında model doğaçlama yaptığı için atıf verilmemeli. Yanlış atıf, "
        "atıfsızlıktan kötüdür. `beklenen kaynak dışı` vekil bir ölçüttür: bir cevap gerçekten "
        "ikinci bir belgeden de beslenebilir.",
        "",
        _table(["Eşik", "Kapsama (cevaplanabilir)", "Doğaçlamaya atıf (uç durum)",
                "Beklenen kaynak dışı"],
               [[f"{r['threshold']:.2f}",
                 f"{r['kapsanan']}/{r['cumle']}" +
                 (f" (%{100 * r['kapsanan'] / r['cumle']:.0f})" if r["cumle"] else ""),
                 f"{r.get('dogaclamaya_atif', 0)}/{r.get('uc_cumle', 0)}",
                 r["beklenen_disi"]] for r in cite_rows]),
        "",
    ]) + "\n"


# ----------------------------------------------------------------------- akış

def run_sweep_report(json_path, out_dir):
    """Kayıtlı koşumdan eşik taraması. LLM çağrılmaz, saniyeler sürer."""
    kayit = json.loads(Path(json_path).read_text(encoding="utf-8"))
    answers = kayit["answers"]
    floors = [0.40, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80]
    cite = [0.40, 0.50, 0.55, 0.60, 0.70, 0.80]
    meta = {"timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "model_id": kayit["meta"]["model_id"], "kaynak": Path(json_path).name}
    rapor = build_sweep_report(meta, grounding_floor_sweep(answers, floors),
                               citation_threshold_sweep(answers, cite))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"esik-taramasi-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    out_path.write_text(rapor, encoding="utf-8")
    print(rapor)
    print(f"Rapor yazıldı: {os.path.relpath(out_path, ROOT)}")


def main():
    ap = argparse.ArgumentParser(description="personas değerlendirme koşumu")
    ap.add_argument("--model", help="sohbet modeli takma adı (varsayılan: config.CHAT_MODEL)")
    ap.add_argument("--esik", help="eşik taraması, virgülle: 0.10,0.15,0.20")
    ap.add_argument("--k", help="K taraması, virgülle: 2,3,5")
    ap.add_argument("--llm-yok", action="store_true", dest="no_llm",
                    help="sohbet modelini çağırma, yalnızca deterministik metrikler")
    ap.add_argument("--cikti", default=str(OUT_DIR), help="rapor klasörü")
    ap.add_argument("--sadakat-tarama", dest="sadakat_tarama", metavar="JSON",
                    help="kayıtlı koşum JSON'u üzerinden sadakat/atıf eşiği taraması")
    args = ap.parse_args()

    if args.sadakat_tarama:
        return run_sweep_report(args.sadakat_tarama, Path(args.cikti))

    questions = load_questions()
    thresholds = [float(x) for x in args.esik.split(",")] if args.esik else [config.SIM_THRESHOLD]
    ks = [int(x) for x in args.k.split(",")] if args.k else [config.TOP_K]
    sweeping = len(thresholds) > 1 or len(ks) > 1

    model_id = config.CHAT_MODEL
    if args.model and not args.no_llm and not sweeping:
        model_id = apply_model(args.model)
    elif args.model:
        config.CHAT_MODEL = model_id = args.model

    print("Deterministik metrikler…", flush=True)
    routing = run_routing(questions)
    scored = score_questions(questions)
    hits, typo, kisa, abstains = run_retrieval(questions, scored, ks[0], thresholds[0])
    sweep = run_sweep(questions, scored, thresholds, ks) if sweeping else []

    print(f"  yönlendirme: {sum(r['ok'] for r in routing)}/{len(routing)}"
          f" · erişim: {sum(h['ok'] for h in hits)}/{len(hits)}"
          f" · yazım hatalı: {sum(h['ok'] for h in typo)}/{len(typo)}"
          f" · kısa sorgu: {sum(h['ok'] for h in kisa)}/{len(kisa)}"
          f" · çekimserlik: {sum(a['ok'] for a in abstains)}/{len(abstains)}", flush=True)
    if sweep:
        best = max(sweep, key=lambda r: (r["balance"], -r["threshold"]))
        print(f"  en iyi denge: K={best['k']} eşik={best['threshold']:.2f} "
              f"(isabet {best['hit']:.0%}, yazım hatalı {best['typo']:.0%}, "
              f"kısa {best['kisa']:.0%}, çekimserlik {best['abstain']:.0%})", flush=True)

    answers = []
    if not args.no_llm and not sweeping:
        print(f"Üretim koşumu ({model_id})…", flush=True)
        answers = run_answers(questions, ANSWER_CATEGORIES)

    chunk_rows = store.all_chunks()
    meta = {
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "model_id": model_id, "k": ks[0], "threshold": thresholds[0],
        "chunks": len(chunk_rows), "sources": len({s for (s, _t, _e) in chunk_rows}),
    }
    report = build_report(meta, routing, hits, typo, kisa, abstains, answers, sweep)

    out_dir = Path(args.cikti)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    suffix = "tarama" if sweeping else str(model_id).split("-generic")[0]
    out_path = out_dir / f"sonuclar-{stamp}-{suffix}.md"
    out_path.write_text(report, encoding="utf-8")
    print(f"Rapor yazıldı: {os.path.relpath(out_path, ROOT)}")

    if answers:
        # Markdown tablosu cevapları kısaltır; elle kalite puanlaması için tam metin gerekir.
        raw_path = out_path.with_suffix(".json")
        raw_path.write_text(
            json.dumps({"meta": meta, "answers": answers}, ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"Tam cevaplar: {os.path.relpath(raw_path, ROOT)}")


if __name__ == "__main__":
    main()
