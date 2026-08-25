import os
import sys

# Proje kökünü import yoluna ekle (python ui/cli.py ile de çalışsın diye).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import assistant, citations  # noqa: E402

MAX_HISTORY = 8  # son dört soru-cevap bellekte tutulur


def citation_lines(result):
    """Cevabın altına yazılacak kaynak ve atıf satırları.

    Terminalde cevap akarak yazıldığı için rozet metnin içine konamaz; onun
    yerine cümle sırasına göre bir harita yazılır. Numaralar web arayüzündeki
    rozetlerle aynıdır (getirilen parçanın sırası).
    """
    parcalar = result.get("chunks") or []
    kaynaklar = list(dict.fromkeys(result.get("sources") or []))
    if not parcalar:
        return [f"  (Kaynak: {', '.join(kaynaklar)})"] if kaynaklar else []

    liste = " · ".join(f"[{i + 1}] {c['source']}" for i, c in enumerate(parcalar))
    satirlar = [f"  Kaynaklar: {liste}"]

    numaralar = {(a["start"], a["end"]): a["chunk"] + 1
                 for a in result.get("citations") or []}
    esli, atifsiz = [], []
    for sira, konum in enumerate(citations.spans(result["text"]), start=1):
        numara = numaralar.get(konum)
        if numara:
            esli.append(f"{sira}→[{numara}]")
        else:
            atifsiz.append(str(sira))
    if esli:
        satir = f"  Atıflar: {' '.join(esli)}"
        if atifsiz:
            satir += f" · atıfsız: {', '.join(atifsiz)}"
        satirlar.append(satir)
    elif atifsiz:
        satirlar.append("  Atıflar: hiçbir cümle getirilen parçaya bağlanamadı")
    return satirlar


def main():
    print("personas — Kişisel Asistan (çıkış için 'q')")
    history = []
    while True:
        try:
            query = input("\nSen> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if query.lower() in ("q", "quit", "çık", "cik"):
            break
        if not query:
            continue

        print("\nAsistan> ", end="", flush=True)
        res, streamed = None, False
        for event in assistant.answer_stream(query, history=history):
            if event["type"] == "token":
                streamed = True
                print(event["text"], end="", flush=True)
            else:
                res = event["result"]
        if not streamed:  # model çağrılmayan akışlar (taslak, "bilgi yok", uygulama açma)
            print(res["text"], end="")
        print()

        for satir in citation_lines(res):
            print(satir)

        history += [("user", query), ("assistant", res["text"])]
        history = history[-MAX_HISTORY:]

        if res["pending_action"]:
            ok = input("Onayla (e/h)> ").strip().lower()
            if ok in ("e", "evet", "y", "yes"):
                print(assistant.confirm(res["pending_action"]))
            else:
                print("İptal edildi.")


if __name__ == "__main__":
    main()
