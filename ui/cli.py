import os
import sys

# Proje kökünü import yoluna ekle (python ui/cli.py ile de çalışsın diye).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import assistant  # noqa: E402


def main():
    print("personas — Kişisel Asistan (çıkış için 'q')")
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
        res = assistant.answer(query)
        print(f"\nAsistan> {res['text']}")
        if res["sources"]:
            print(f"  (Kaynak: {', '.join(res['sources'])})")
        if res["pending_action"]:
            ok = input("Onayla (e/h)> ").strip().lower()
            if ok in ("e", "evet", "y", "yes"):
                print(assistant.confirm(res["pending_action"]))
            else:
                print("İptal edildi.")


if __name__ == "__main__":
    main()
