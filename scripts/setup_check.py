import os
import shutil

from app import llm, store


def check(name, fn):
    try:
        fn()
        print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")


def _check_foundry():
    if shutil.which("foundry") is None and not os.path.exists("/opt/homebrew/bin/foundry"):
        raise RuntimeError("foundry PATH'te bulunamadı")


def main():
    check("Foundry Local kurulu", _check_foundry)
    check("Chat modeli yanıt veriyor", lambda: llm.chat("Kısa cevap ver.", "merhaba"))
    check("Embedding üretiliyor", lambda: llm.embed(["deneme"]))
    check("Veritabanı yazılabilir", lambda: (store.init_db(), store.count()))


if __name__ == "__main__":
    main()
