"""Kanun PDF'lerini bilgi tabanına yükler.

    python scripts/mevzuat_yukle.py              data/mevzuat altındaki tüm kanunlar
    python scripts/mevzuat_yukle.py --temizle    önce eski bilgi tabanını sil

Metinler mevzuat.gov.tr'den indirilmiş, değişiklikleri işlenmiş güncel
hâllerdir. Hiçbir madde elle yazılmaz ya da özetlenmez; PDF'ten çıkan metin
birebir saklanır.
"""
import argparse
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KOK))

from app import ingest, mevzuat, store  # noqa: E402

MEVZUAT_DIR = KOK / "data" / "mevzuat"


def main():
    ap = argparse.ArgumentParser(description="Kanun metinlerini yükle")
    ap.add_argument("--klasor", default=str(MEVZUAT_DIR))
    ap.add_argument("--temizle", action="store_true",
                    help="yüklemeden önce bilgi tabanını tamamen sil")
    args = ap.parse_args()

    klasor = Path(args.klasor)
    pdfler = sorted(klasor.glob("*.pdf"))
    if not pdfler:
        raise SystemExit(f"PDF bulunamadı: {klasor}")

    store.init_db()
    if args.temizle:
        store.clear()
        print("Bilgi tabanı temizlendi.")

    toplam = 0
    basladi = time.perf_counter()
    for yol in pdfler:
        metin = ingest.read_document(yol)
        bilgi = mevzuat.kanun_bilgisi(metin)
        ad = f"{bilgi.numara} sayılı {mevzuat.turkce_baslik(bilgi.ad)}"
        t = time.perf_counter()
        sonuc = ingest.ingest_mevzuat_text(metin, kaynak=ad)
        toplam += sonuc["chunks"]
        maddeler = len({p.madde for p in mevzuat.parcala(metin)})
        print(f"  {ad[:48]:50s} {maddeler:5d} madde → {sonuc['chunks']:5d} parça "
              f"({time.perf_counter() - t:5.1f} sn)", flush=True)

    print(f"\nToplam {toplam} parça · {time.perf_counter() - basladi:.1f} saniye")
    for kaynak, adet in store.sources():
        print(f"  {adet:5d}  {kaynak}")


if __name__ == "__main__":
    main()
