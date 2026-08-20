import os
import sys

# Proje kökünü import yoluna ekle (python ui/cli.py ile de çalışsın diye).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import assistant  # noqa: E402

MAX_HISTORY = 8  # son dört soru-cevap bellekte tutulur


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

        if res["sources"]:
            print(f"  (Kaynak: {', '.join(dict.fromkeys(res['sources']))})")

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
