from app import assistant


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
