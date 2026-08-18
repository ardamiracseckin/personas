# personas — Kişisel Asistan (offline)

Mac'inde **tamamen internetsiz** çalışan kişisel asistan. Dört işi yapar:

1. **Belge Soru-Cevap (RAG):** `data/documents/` içindeki kendi belgelerinden kaynak göstererek cevap verir; bilmediğinde "bilmiyorum" der.
2. **Takvim:** Apple Takvim'i okur ve özetler; **onayınla** yeni etkinlik ekler.
3. **Mail:** Apple Mail'i okur ve özetler; **onayınla** e-posta gönderir.
4. **Uygulama açma:** "Spotify aç", "hesap makinesi aç" gibi komutlarla Mac uygulamalarını açar.

Asistanın "beyni" [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/) ile cihazda çalışan bir LLM'dir (bulut/Azure yok). Embedding'ler `fastembed` ile yereldir — Foundry Local kataloğunda embedding görevine sahip model bulunmuyor.

Bilgi tabanı 8 Türkçe teknik nottan oluşur ve ingest sonrası 58 parçaya bölünür. Erişim ayarları
(`TOP_K = 3`, `SIM_THRESHOLD = 0.40`) tahminle değil, 30 soruluk bir set üzerinde ölçülerek
seçilmiştir; ayrıntı için [değerlendirme raporu](docs/eval/degerlendirme-raporu.md).

> Yazma işlemleri (etkinlik ekleme, mail gönderme) **asla onay olmadan** yapılmaz. Silme yoktur.

## Mimari

```
Soru → router (belge? takvim? mail? sohbet?) → bağlam topla / taslak çıkar
     → Foundry Local LLM cevabı üretir → CLI veya Web'de göster
```

Modüller: `app/config.py`, `store.py`, `chunking.py`, `similarity.py`, `llm.py`,
`ingest.py`, `retriever.py`, `router.py`, `assistant.py`, `app/tools/{applescript,calendar_tool,mail_tool,app_launcher}.py`.
Arayüzler: `ui/cli.py`, `ui/web.py`.

## Kurulum

```bash
# 1) Homebrew (yoksa)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2) Foundry Local + sohbet modeli
brew install microsoft/foundrylocal/foundrylocal
foundry model download phi-4-mini

# 3) Python ortamı
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 4) Belgeleri yükle (embedding modeli ilk çalıştırmada bir kez iner)
python -m app.ingest
```

Modelleri kontrol etmek için: `foundry model list`. Kullanılan aliaslar `app/config.py` içindedir
(`CHAT_MODEL = "phi-4-mini"`, embedding: `paraphrase-multilingual-MiniLM-L12-v2`).

**Daha hafif donanım için:** `phi-4-mini` 3,7 GB yer kaplar ve p50 3,95 sn sürer. 8 GB bellek
zorlanıyorsa `app/config.py` içinde `CHAT_MODEL = "qwen2.5-1.5b"` yapın (1,5 GB, p50 2,45 sn);
karşılığında cevap doğruluğu 22/28'den 18/28'e düşer. Karşılaştırmanın tamamı değerlendirme
raporundadır.

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

## Testler ve değerlendirme

```bash
python -m pytest -q                  # 63 test (birim + soru seti regresyonu)
```

Uçtan uca değerlendirme koşumu, `eval/questions.json` içindeki 30 soruyu çalıştırıp
`docs/eval/` altına markdown rapor ve tam cevapların JSON dökümünü yazar:

```bash
python scripts/evaluate.py                        # tam koşum (model gerekir)
python scripts/evaluate.py --llm-yok              # sadece deterministik metrikler, saniyeler sürer
python scripts/evaluate.py --esik 0.30,0.40,0.50  # eşik taraması
python scripts/evaluate.py --model qwen2.5-1.5b   # başka modelle karşılaştırma
```

Ölçülen metrikler: yönlendirme doğruluğu, erişim isabeti (hit@K), cevaplanamaz sorularda
çekimserlik ve gecikme (p50/p95).

## Teslimler

| Dosya | İçerik |
|---|---|
| [`docs/eval/degerlendirme-raporu.md`](docs/eval/degerlendirme-raporu.md) | Ölçüm yöntemi, eşik taraması, model karşılaştırması, kalan zayıflıklar |
| [`docs/rapor/personas-proje-raporu.docx`](docs/rapor/personas-proje-raporu.docx) | Proje raporu (Word). Üreteci: `docs/rapor/rapor_uret.js` |
| [`docs/sunum/index.html`](docs/sunum/index.html) | Demo sunumu — çevrimdışı açılır, ok tuşlarıyla gezilir |
| `docs/eval/sonuclar-*.md` / `.json` | Ham koşum çıktıları |

## Sınırlar

- Küçük yerel model (8 GB RAM'e uygun) → genel bilgi/sohbet ChatGPT kadar güçlü değildir; en iyi kendi belgelerinden cevaplarken çalışır.
- Takvim/Mail entegrasyonu yalnızca **Apple** uygulamaları içindir (macOS).
- Seçilen model, bilgi tabanı dışındaki sorularda nadiren kendi genel bilgisinden cevap verebiliyor;
  bu tür cevaplarda kaynak gösterilmez (ölçüm: 6 cevaplanamaz sorunun 1'i).
- Belge biçimi `.txt` ve `.md` ile sınırlıdır; PDF işleme kapsam dışıdır.

Tasarım dokümanı: `docs/specs/2026-07-03-kisisel-asistan-design.md` ·
Uygulama planı: `docs/plans/2026-07-03-personas-implementation-plan.md`
