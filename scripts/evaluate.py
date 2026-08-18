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

from app import assistant, config, llm, router, store  # noqa: E402
from app.similarity import cosine  # noqa: E402

QUESTIONS_PATH = ROOT / "eval" / "questions.json"
OUT_DIR = ROOT / "docs" / "eval"
ANSWER_CATEGORIES = ("cevaplanabilir", "cevaplanamaz", "uc_durum")

# Çekimserlik iki katmanda oluşabilir: erişim eşiği hiç parça bırakmazsa asistan
# sabit NO_INFO metnini döndürür; parça geldiği hâlde bağlam yetersizse modelin
# kendisi istemdeki kural gereği bilmediğini söyler. İkincisi serbest metindir.
ABSTAIN_RE = re.compile(r"bilgi(m)? yok|bilmiyorum|bulamadım", re.IGNORECASE)


def is_abstention(text):
    return bool(ABSTAIN_RE.search(text or ""))


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
    """Her soru için (kaynak, skor) sıralı listesi. Tek embedding turu, LLM yok."""
    chunks = store.all_chunks()
    if not chunks:
        raise SystemExit("Veritabanı boş. Önce 'python -m app.ingest' çalıştırın.")
    texts = [q["question"] for q in questions]
    vectors = llm.embed(texts)
    scored = {}
    for q, qvec in zip(questions, vectors):
        rows = [(src, cosine(qvec, emb)) for (src, _text, emb) in chunks]
        rows.sort(key=lambda r: r[1], reverse=True)
        scored[q["id"]] = rows
    return scored


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


def run_retrieval(questions, scored, k, threshold):
    """Cevaplanabilir sorularda hit@k, cevaplanamaz sorularda çekimserlik."""
    hits, abstains = [], []
    for q in by_category(questions, "cevaplanabilir"):
        top = [(s, sc) for (s, sc) in scored[q["id"]] if sc >= threshold][:k]
        hits.append({
            "id": q["id"], "question": q["question"],
            "expected": q["expected_source"],
            "got": [s for (s, _sc) in top],
            "best_score": scored[q["id"]][0][1],
            "ok": any(s == q["expected_source"] for (s, _sc) in top),
        })
    for q in by_category(questions, "cevaplanamaz"):
        top = [(s, sc) for (s, sc) in scored[q["id"]] if sc >= threshold][:k]
        abstains.append({
            "id": q["id"], "question": q["question"],
            "best_score": scored[q["id"]][0][1],
            "ok": not top,  # eşiği geçen parça yoksa asistan "bilgim yok" der
        })
    return hits, abstains


def run_sweep(questions, scored, thresholds, ks):
    rows = []
    for k in ks:
        for t in thresholds:
            hits, abstains = run_retrieval(questions, scored, k, t)
            hit_rate = sum(h["ok"] for h in hits) / len(hits)
            abstain_rate = sum(a["ok"] for a in abstains) / len(abstains)
            rows.append({
                "k": k, "threshold": t, "hit": hit_rate, "abstain": abstain_rate,
                "balance": (hit_rate + abstain_rate) / 2,
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
            res = assistant.answer(q["question"])
            text, sources, error = res["text"], res["sources"], None
        except Exception as e:  # uç durumlar çökmemeli; çökerse rapora yazılır
            text, sources, error = "", [], f"{type(e).__name__}: {e}"
        elapsed = time.perf_counter() - started
        rows.append({
            "id": q["id"], "category": q["category"], "question": q["question"],
            "expected_source": q.get("expected_source"), "text": text,
            "sources": sources, "seconds": elapsed, "error": error,
            "abstained": is_abstention(text),
            "abstained_by": ("erişim" if text.strip() == assistant.NO_INFO
                             else "model" if is_abstention(text) else None),
        })
        flag = "!" if error else ("~" if is_abstention(text) else "+")
        print(f"  [{flag}] {q['id']} {elapsed:5.2f}s  {q['question'][:52]}", flush=True)
    return rows


# ---------------------------------------------------------------------- rapor

def _table(header, rows):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build_report(meta, routing, hits, abstains, answers, sweep):
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

    if abstains:
        rate = sum(a["ok"] for a in abstains) / len(abstains)
        lines += [f"## Çekimserlik (cevaplanamaz sorular) — {rate:.0%} ({sum(a['ok'] for a in abstains)}/{len(abstains)})",
                  "", _table(["ID", "Soru", "En yüksek skor", "Eşiğin altında mı"], [
                      [a["id"], a["question"][:48], f"{a['best_score']:.3f}", ok(a["ok"])]
                      for a in abstains]), ""]

    if sweep:
        best = max(sweep, key=lambda r: (r["balance"], -r["threshold"]))
        lines += ["## Eşik / K taraması", "",
                  _table(["K", "Eşik", "Erişim isabeti", "Çekimserlik", "Denge"], [
                      [r["k"], f"{r['threshold']:.2f}", f"{r['hit']:.0%}",
                       f"{r['abstain']:.0%}", f"{r['balance']:.0%}"] for r in sweep]),
                  "", f"En iyi denge: **K={best['k']}, eşik={best['threshold']:.2f}** "
                      f"(isabet {best['hit']:.0%}, çekimserlik {best['abstain']:.0%})", ""]

    if answers:
        times = [a["seconds"] for a in answers]
        errors = [a for a in answers if a["error"]]
        unans = [a for a in answers if a["category"] == "cevaplanamaz"]
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
                  ]), "",
                  "Kalite puanı elle doldurulur: 2 = doğru ve yeterli, 1 = kısmen doğru, 0 = yanlış/alakasız.",
                  "", _table(["ID", "Kategori", "Soru", "Cevap", "Kaynaklar", "Süre", "Puan"], [
                      [a["id"], a["category"], a["question"][:40] or "(boş)",
                       (a["error"] or a["text"]).replace("\n", " ")[:110],
                       ", ".join(dict.fromkeys(a["sources"])) or "—",
                       f"{a['seconds']:.2f}", " "]
                      for a in answers]), ""]

    return "\n".join(lines) + "\n"


# ----------------------------------------------------------------------- akış

def main():
    ap = argparse.ArgumentParser(description="personas değerlendirme koşumu")
    ap.add_argument("--model", help="sohbet modeli takma adı (varsayılan: config.CHAT_MODEL)")
    ap.add_argument("--esik", help="eşik taraması, virgülle: 0.10,0.15,0.20")
    ap.add_argument("--k", help="K taraması, virgülle: 2,3,5")
    ap.add_argument("--llm-yok", action="store_true", dest="no_llm",
                    help="sohbet modelini çağırma, yalnızca deterministik metrikler")
    ap.add_argument("--cikti", default=str(OUT_DIR), help="rapor klasörü")
    args = ap.parse_args()

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
    hits, abstains = run_retrieval(questions, scored, ks[0], thresholds[0])
    sweep = run_sweep(questions, scored, thresholds, ks) if sweeping else []

    print(f"  yönlendirme: {sum(r['ok'] for r in routing)}/{len(routing)}"
          f" · erişim: {sum(h['ok'] for h in hits)}/{len(hits)}"
          f" · çekimserlik: {sum(a['ok'] for a in abstains)}/{len(abstains)}", flush=True)
    if sweep:
        best = max(sweep, key=lambda r: (r["balance"], -r["threshold"]))
        print(f"  en iyi denge: K={best['k']} eşik={best['threshold']:.2f} "
              f"(isabet {best['hit']:.0%}, çekimserlik {best['abstain']:.0%})", flush=True)

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
    report = build_report(meta, routing, hits, abstains, answers, sweep)

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
