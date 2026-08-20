# personas — Kişisel Asistan (offline)

Mac'inde **tamamen internetsiz** çalışan kişisel asistan. Dört işi yapar:

1. **Belge Soru-Cevap (RAG):** `data/documents/` içindeki kendi belgelerinden kaynak göstererek cevap verir; bilmediğinde "bilmiyorum" der.
2. **Takvim:** Apple Takvim'i okur ve özetler; **onayınla** yeni etkinlik ekler.
3. **Mail:** Apple Mail'i okur ve özetler; **onayınla** e-posta gönderir.
4. **Uygulama açma:** "Spotify aç", "hesap makinesi aç" gibi komutlarla Mac uygulamalarını açar.

Asistanın "beyni" [Microsoft Foundry Local](https://learn.microsoft.com/azure/ai-foundry/foundry-local/)
ile cihazda çalışan bir LLM'dir (bulut/Azure yok). Embedding'ler `fastembed` ile yereldir — Foundry
Local kataloğunda embedding görevine sahip model bulunmuyor.

Bilgi tabanı 8 Türkçe teknik nottan oluşur ve ingest sonrası 58 parçaya bölünür. Erişim ayarları
(`TOP_K = 3`, `SIM_THRESHOLD = 0.34`) tahminle değil, 44 soruluk bir set üzerinde ölçülerek
seçilmiştir; ayrıntı için [değerlendirme raporu](docs/eval/degerlendirme-raporu.md).

> Yazma işlemleri (etkinlik ekleme, mail gönderme) **asla onay olmadan** yapılmaz. Silme yoktur.

## Arayüz

Tarayıcıda açılan tek sayfa bir uygulama; hiçbir dış kaynağa (CDN dâhil) bağlanmaz.

- Cevaplar **akarak** yazılır, markdown ve kod blokları biçimlendirilir (dil etiketi + kopyala).
- **Sohbetler kalıcıdır**: soldaki listeden geçmiş sohbetlere dönülür, yeniden adlandırılır, silinir.
  Başlığı ilk cevaptan sonra model üretir.
- **Kaynak rozetine tıklayınca** cevabın dayandığı parça metniyle birlikte açılır.
- **Belge sürükle-bırak** ile bilgi tabanına anında eklenir (`.md`, `.txt`, `.pdf`).
- Soldaki menüden **model değiştirilebilir** (8 GB bellekte tek model yüklü kalır, geçiş 20-30 sn).
- **Durdur / yeniden üret / kopyala**, `Cmd+K` yeni sohbet, `Esc` durdurur.
- Asistan **son iki turu hatırlar**: "Python'da sanal ortam nasıl oluşturulur?" → "Peki onu nasıl
  kapatırım?" çalışır.
- Arama **yazım hatalarına dayanıklıdır**: "ekran görünütsünü bölgden nasıl alrım" doğru notu bulur.

## Mimari

```
Soru → router (belge? takvim? mail? uygulama?) → bağlam topla / taslak çıkar
     → Foundry Local LLM cevabı üretir → tarayıcıya akıtılır (SSE)
```

- `app/` — iş mantığı: `config`, `store`, `chat_store`, `chunking`, `similarity`, `lexical`,
  `llm`, `models`, `ingest`, `retriever`, `router`, `assistant`,
  `tools/{applescript,calendar_tool,mail_tool,app_launcher}.py`
- `server/` — FastAPI (`main.py`) ve tek sayfa arayüz (`static/`)
- `ui/cli.py` — terminal arayüzü

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

**Daha hafif donanım için:** `phi-4-mini` 3,7 GB yer kaplar. 8 GB bellek zorlanıyorsa arayüzdeki
model menüsünden `qwen2.5-1.5b` seçilebilir (1,5 GB, belirgin daha hızlı); karşılığında cevap
doğruluğu düşer. Karşılaştırmanın tamamı değerlendirme raporundadır.

## Kullanım

```bash
# Web arayüzü
uvicorn server.main:app --port 8000      # → http://localhost:8000

# Terminal arayüzü
python -m ui.cli
```

Örnek sorular: "Ekran görüntüsünü belirli bir bölgeden nasıl alırım?",
"git'te son commit'i nasıl geri alırım?", "Bugün takvimimde ne var?",
"Cuma 14:30 dişçi randevusu ekle".

## İzinler (Takvim / Mail)

İlk kullanımda macOS **Automation** izni ister:
**System Settings > Privacy & Security > Automation** → Terminal'e Mail/Takvim erişimi ver.

## Testler ve değerlendirme

```bash
python -m pytest -q                  # 167 test (birim, HTTP katmanı, soru seti regresyonu)
```

Değerlendirme koşumu `eval/questions.json` içindeki 44 soruyu çalıştırıp `docs/eval/` altına
markdown rapor ve tam cevapların JSON dökümünü yazar:

```bash
python scripts/evaluate.py                        # tam koşum (model gerekir)
python scripts/evaluate.py --llm-yok              # sadece deterministik metrikler, saniyeler sürer
python scripts/evaluate.py --esik 0.30,0.34,0.40  # eşik taraması
python scripts/evaluate.py --model qwen2.5-1.5b   # başka modelle karşılaştırma
```

Ölçülen metrikler: yönlendirme doğruluğu, erişim isabeti (hit@K), **yazım hatalı sorularda erişim**,
cevaplanamaz sorularda çekimserlik, gecikme (p50/p95) ve **otomatik kalite puanı** —
cevaplanabilir sorulardaki `expected_substrings` alanına göre 0–2 puan. Model değiştirip koşumu
tekrarlamak yeterli, elle puanlama gerekmez.

## Teslimler

| Dosya | İçerik |
|---|---|
| [`docs/eval/degerlendirme-raporu.md`](docs/eval/degerlendirme-raporu.md) | Ölçüm yöntemi, eşik taraması, model karşılaştırması, kalan zayıflıklar |
| [`docs/rapor/personas-proje-raporu.docx`](docs/rapor/personas-proje-raporu.docx) | Proje raporu (Word). Üreteci: `docs/rapor/rapor_uret.js` |
| [`docs/sunum/index.html`](docs/sunum/index.html) | Demo sunumu — çevrimdışı açılır, ok tuşlarıyla gezilir |
| `docs/eval/sonuclar-*.md` / `.json` | Ham koşum çıktıları |

## Sınırlar

- Küçük yerel model (8 GB RAM'e uygun) → genel bilgi/sohbet ChatGPT kadar güçlü değildir; en iyi
  kendi belgelerinden cevaplarken çalışır.
- Takvim/Mail entegrasyonu yalnızca **Apple** uygulamaları içindir (macOS).
- **Görsel yükleme henüz kapalı:** kod hazır (`llm.chat_stream(..., image_b64=...)`), ancak kurulu
  Foundry Local 0.8.119 görsel modelleri yükleyemiyor (`genai_config.json` şeması tanınmıyor).
  Çalışma zamanı 0.10.x'e yükseltilince açılabilir.
- Model seçimi süreç ömrü boyunca geçerlidir; sunucu yeniden başlatılınca `config.CHAT_MODEL`
  varsayılanına döner.
- Sohbet geçmişinde kaynak parçalarının metni saklanmaz; parça paneli yalnızca canlı cevaplarda dolu gelir.

Tasarım dokümanı: `docs/specs/2026-07-03-kisisel-asistan-design.md` ·
Uygulama planı: `docs/plans/2026-07-03-personas-implementation-plan.md`
