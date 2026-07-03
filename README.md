# personas — Kişisel Asistan (offline)

Mac'inde **tamamen internetsiz** çalışan kişisel asistan. Üç işi yapar:

1. **Belge Soru-Cevap (RAG):** `data/documents/` içindeki kendi belgelerinden kaynak göstererek cevap verir; bilmediğinde "bilmiyorum" der.
2. **Takvim:** Apple Takvim'i okur ve özetler; **onayınla** yeni etkinlik ekler.
3. **Mail:** Apple Mail'i okur ve özetler; **onayınla** e-posta gönderir.

Asistanın "beyni" [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/) ile cihazda çalışan bir LLM'dir (bulut/Azure yok). Embedding'ler `fastembed` ile yereldir.

> Yazma işlemleri (etkinlik ekleme, mail gönderme) **asla onay olmadan** yapılmaz. Silme yoktur.

## Mimari

```
Soru → router (belge? takvim? mail? sohbet?) → bağlam topla / taslak çıkar
     → Foundry Local LLM cevabı üretir → CLI veya Web'de göster
```

Modüller: `app/config.py`, `store.py`, `chunking.py`, `similarity.py`, `llm.py`,
`ingest.py`, `retriever.py`, `router.py`, `assistant.py`, `app/tools/{applescript,calendar_tool,mail_tool}.py`.
Arayüzler: `ui/cli.py`, `ui/web.py`.

## Kurulum

```bash
# 1) Homebrew (yoksa)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2) Foundry Local + sohbet modeli
brew install microsoft/foundrylocal/foundrylocal
foundry model download phi-3.5-mini

# 3) Python ortamı
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4) Belgeleri yükle (embedding modeli ilk çalıştırmada bir kez iner)
python -m app.ingest
```

Modelleri kontrol etmek için: `foundry model list`. Kullanılan aliaslar `app/config.py` içindedir
(`CHAT_MODEL = "phi-3.5-mini"`, embedding: `paraphrase-multilingual-MiniLM-L12-v2`).

## Kullanım

```bash
# Terminal arayüzü
python -m ui.cli

# Web arayüzü
streamlit run ui/web.py
```

Örnek sorular: "Ekran görüntüsünü belirli bir bölgeden nasıl alırım?",
"git'te son commit'i nasıl geri alırım?", "Bugün takvimimde ne var?",
"Yarın 15:00 dişçi randevusu ekle".

## İzinler (Takvim / Mail)

İlk kullanımda macOS **Automation** izni ister:
**System Settings > Privacy & Security > Automation** → Terminal'e Mail/Takvim erişimi ver.

## Testler

```bash
python -m pytest -q
```

## Sınırlar

- Küçük yerel model (8 GB RAM'e uygun) → genel bilgi/sohbet ChatGPT kadar güçlü değildir; en iyi kendi belgelerinden cevaplarken çalışır.
- Takvim/Mail entegrasyonu yalnızca **Apple** uygulamaları içindir (macOS).

Tasarım dokümanı: `docs/specs/2026-07-03-kisisel-asistan-design.md` ·
Uygulama planı: `docs/plans/2026-07-03-personas-implementation-plan.md`
