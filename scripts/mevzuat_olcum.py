"""Mevzuat asistanının ölçümü.

Model çağrılmaz: asistan cevap üretmiyor, madde çıkarıyor. Ölçülen şey erişimin
doğru maddeyi bulup bulmadığı ve alakasız soruları reddedip reddetmediğidir.

    python scripts/mevzuat_olcum.py
    python scripts/mevzuat_olcum.py --k 5

Beklenen madde numaraları korpustaki başlıklardan doğrulanmıştır (bkz.
tests/test_mevzuat_soru_seti.py).
"""
import argparse
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from app import mevzuat_yanit, retriever, store  # noqa: E402

SORU_YOLU = KOK / "eval" / "mevzuat_sorular.json"
CIKTI = KOK / "docs" / "olcum"


def sorular():
    return json.loads(SORU_YOLU.read_text(encoding="utf-8"))["questions"]


def kategoriden(hepsi, ad):
    return [s for s in hepsi if s["category"] == ad]


def hedef_mi(kunye, kanun, madde):
    return bool(re.match(rf"^{kanun} sayılı .* md\. {re.escape(madde)}(?: |—|$)", kunye))


def adaylarin_kunyeleri(yanit):
    if yanit.birincil is None:      # bulunamadı ya da kapsam dışı reddi
        return []
    return [f"{a.atif} — {a.baslik}" for a in [yanit.birincil] + yanit.digerleri]


def olc(hepsi, k):
    satirlar = []
    for s in hepsi:
        t0 = time.perf_counter()
        yanit = mevzuat_yanit.sor(s["question"], k=k)
        sure = time.perf_counter() - t0
        kunyeler = adaylarin_kunyeleri(yanit)
        satir = {"id": s["id"], "category": s["category"], "question": s["question"],
                 "seconds": sure, "aday_sayisi": len(kunyeler),
                 "adaylar": kunyeler, "bulunamadi": yanit.bulunamadi,
                 "tavsiye_reddi": yanit.tavsiye_reddi}
        if s["category"] == "cevaplanabilir":
            yerler = [i + 1 for i, ky in enumerate(kunyeler)
                      if hedef_mi(ky, s["kanun"], s["madde"])]
            satir.update({"kanun": s["kanun"], "madde": s["madde"], "alan": s["alan"],
                          "sira": yerler[0] if yerler else None,
                          "dogru_kanun": bool(kunyeler) and kunyeler[0].startswith(s["kanun"])})
            satir["one_cikan"] = yanit.birincil.one_cikan if kunyeler else ""
        satirlar.append(satir)
    return satirlar


def rapor(satirlar, k, parca, kaynak_sayisi):
    cevaplanabilir = [s for s in satirlar if s["category"] == "cevaplanabilir"]
    disinda = [s for s in satirlar if s["category"] == "cevaplanamaz"]
    tahmin = [s for s in satirlar if s["category"] == "tahmin"]
    uc = [s for s in satirlar if s["category"] == "uc_durum"]
    sureler = [s["seconds"] for s in satirlar]

    def hit(n):
        return sum(1 for s in cevaplanabilir if s["sira"] and s["sira"] <= n)

    satir = ["| Ölçüt | Sonuç |", "|---|---|",
             f"| Bilgi tabanı | {parca} parça / {kaynak_sayisi} kanun |",
             f"| Doğru madde 1. sırada | {hit(1)}/{len(cevaplanabilir)} "
             f"(%{100*hit(1)/len(cevaplanabilir):.0f}) |",
             f"| Doğru madde ilk 3'te | {hit(3)}/{len(cevaplanabilir)} |",
             f"| Doğru madde ilk {k}'te | {hit(k)}/{len(cevaplanabilir)} |",
             f"| Doğru kanundan aday geldi | "
             f"{sum(1 for s in cevaplanabilir if s['dogru_kanun'])}/{len(cevaplanabilir)} |",
             f"| Hukuk dışı soruda çekimserlik | "
             f"{sum(1 for s in disinda if s['bulunamadi'])}/{len(disinda)} |",
             f"| Tavsiye isteyen soruda ret | "
             f"{sum(1 for s in tahmin if s['tavsiye_reddi'])}/{len(tahmin)} |",
             f"| Uç durumda çökme | 0/{len(uc)} |",
             f"| Ortalama süre | {statistics.mean(sureler):.2f} sn |",
             f"| p95 süre | {sorted(sureler)[int(0.95*(len(sureler)-1))]:.2f} sn |"]
    return satir, cevaplanabilir, disinda, tahmin, uc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    if store.count() == 0:
        raise SystemExit("Bilgi tabanı boş: python scripts/mevzuat_yukle.py")
    hepsi = sorular()
    print(f"{len(hepsi)} soru ölçülüyor…", flush=True)
    retriever.get_top_chunks("ısınma")           # ilk çağrı dizini kurar
    satirlar = olc(hepsi, args.k)
    tablo, cevaplanabilir, disinda, tahmin, uc = rapor(
        satirlar, args.k, store.count(), len(store.sources()))
    print("\n".join(tablo))

    print("\nAlan bazında doğru madde 1. sırada:")
    alanlar = {}
    for s in cevaplanabilir:
        d = alanlar.setdefault(s["alan"], [0, 0])
        d[1] += 1
        d[0] += 1 if s["sira"] == 1 else 0
    for alan, (dogru, toplam) in sorted(alanlar.items()):
        print(f"  {alan:10s} {dogru}/{toplam}")

    print("\nDoğru maddeyi hiç bulamadıkları:")
    for s in cevaplanabilir:
        if not s["sira"]:
            print(f"  {s['id']} {s['question'][:44]:46s} → beklenen {s['kanun']} md.{s['madde']}"
                  f" · gelen: {(s['adaylar'][0][:44] if s['adaylar'] else '—')}")

    print("\nTahmin isteyen sorulara ne oldu:")
    for s in tahmin:
        if s["tavsiye_reddi"]:
            durum = "kapsam dışı diye reddetti"
        elif s["bulunamadi"]:
            durum = "ilgili madde bulamadı"
        else:
            durum = f"{s['aday_sayisi']} aday gösterdi"
        print(f"  {s['id']} {s['question'][:40]:42s} → {durum}")

    CIKTI.mkdir(parents=True, exist_ok=True)
    yol = CIKTI / f"mevzuat-{datetime.now().strftime('%Y%m%d-%H%M')}.json"
    yol.write_text(json.dumps({"k": args.k, "satirlar": satirlar}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\nHam çıktı: {yol.relative_to(KOK)}")


if __name__ == "__main__":
    main()
