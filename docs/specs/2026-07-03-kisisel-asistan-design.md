# Tasarım Dokümanı: personas — Kişisel Asistan (offline-öncelikli, yerel RAG + araçlar)

**Tarih:** 2026-07-03
**Proje adı:** `personas` ("personal assistant" kısaltması)
**Proje kökü:** `MICROSFT PROJE RAG/personas`
**Staj bağlamı:** "One-Month Project Plan: Local RAG AI Assistant with Microsoft Foundry Local"

---

## 1. Amaç

Kullanıcının Mac'inde (Apple M2, 8 GB RAM, macOS 26) çalışan, **internetsiz/offline** bir kişisel asistan. Üç yeteneği var:

1. **Belge Q&A (RAG)** — Kullanıcının kendi belge/notlarından kaynak-temelli cevap verir. *(Stajın çekirdek teslimi.)*
2. **Takvim** — Apple Takvim'deki etkinlikleri **okur** ve özetler; ayrıca **onaylı** etkinlik ekler. *(Bonus araç.)*
3. **Mail** — Apple Mail'i **okur** ve özetler; ayrıca **onaylı** e-posta gönderir. *(Bonus araç.)*

Asistanın "beyni" **Foundry Local** ile çalışan yerel bir LLM'dir. Bulut/Azure/API **kullanılmaz**. Geliştirme aracı olarak Claude Code kullanılır; bu, projenin *içinde* çalışan modelle karıştırılmamalıdır.

### Kapsam kararı ve bilinen risk
Kullanıcı, staj planındaki saf offline-RAG kapsamının ötesine geçerek takvim + mail entegrasyonu istedi (bilinçli karar, riski kendisine iletildi). Uzlaşı: RAG çekirdeği stajın istediğini birebir karşılar; takvim/mail birer "araç" olarak eklenir ve asistanı bir *agent* örneğine dönüştürür.

**Yetki: okuma + yazma (insan onaylı).** Okuma serbesttir. Yazma işlemleri (etkinlik ekleme, e-posta gönderme) **asla kullanıcı onayı olmadan yapılmaz**: asistan taslağı hazırlar, kullanıcıya gösterir, kullanıcı açıkça onaylayınca işlem gerçekleşir (human-in-the-loop). Toplu silme veya onaysız otomatik işlem yoktur.

---

## 2. Teknoloji ve donanım kısıtları

| Konu | Karar / Not |
|---|---|
| İşlemci | Apple M2 (arm64) — Foundry Local destekli |
| RAM | 8 GB — **sadece küçük modeller**; aynı anda tek büyük model yüklenir |
| macOS | 26.5.1 |
| Python | Sistemde 3.14.5 var; venv kurulur. ⚠️ 3.14 çok yeni — bir bağımlılık uyumsuzsa Python 3.12 venv'e düşülür |
| Homebrew | Yok → kurulacak → `brew install foundrylocal` |
| Chat modeli | Küçük (ör. Phi-3.5-mini / benzeri). Kesin katalog adı kurulumda `foundry model list` ile doğrulanır |
| Embedding modeli | Küçük (ör. qwen3-embedding-0.6b). Yoksa yerel `sentence-transformers` (all-MiniLM-L6-v2) fallback |
| Veritabanı | SQLite (tek dosya, sunucusuz) |
| Arayüz | İkisi de: CLI (terminal) + Streamlit (web sohbet) |
| E-posta/Takvim | Apple Mail + Apple Calendar, AppleScript (`osascript`). Okuma + **onaylı** yazma (etkinlik ekleme, mail gönderme) |
| Sürüm kontrolü | Git + **gizli (private)** GitHub reposu `personas` ("personal assistant" kısaltması). `gh` CLI Homebrew ile kurulur; tek seferlik `gh auth login` gerekir |

---

## 3. Mimari

Tek makinede, katmanlı ve modüler. Her modülün tek sorumluluğu vardır.

```
Kullanıcı sorusu (CLI veya Web)
        │
        ▼
   ROUTER (router.py)  ── "Bu soru: belge? takvim? mail? sohbet?"
        │
        ├── belge  → retriever.get_top_chunks(q)   → ilgili not parçaları
        ├── takvim → calendar_tool.get_events(...) → etkinlik listesi
        ├── mail   → mail_tool.get_recent(...)     → e-posta özetleri
        └── sohbet → (harici bağlam yok)
        │
        ▼
   ASSISTANT (assistant.py)  ── sistem talimatı + bağlam + soru → prompt
        │
        ▼
   LLM (llm.py → Foundry Local)  ── cevabı üretir (kaynak belirterek)
        │
        ▼
   Cevap → CLI veya Web'de gösterilir
```

### Yönlendirme (router) mantığı — iki katmanlı
Küçük modelin "araç seçimi"nde şaşırmasını önlemek için:
1. **Kural katmanı:** anahtar kelimeler ("takvim, etkinlik, toplantı, bugün ne var, yarın" → takvim; "mail, e-posta, gelen kutusu, okunmamış" → mail).
2. **Niyet katmanı (okuma/yazma):** fiillere bakılır ("ekle, oluştur, kur" → takvim-yazma; "gönder, yaz, ilet" → mail-yazma). Yazma niyeti → taslak üretilir, doğrudan işlenmez.
3. **Model katmanı:** kural eşleşmezse LLM'e kısa, few-shot bir sınıflandırma promptu ile sorulur.
4. **Varsayılan:** hiçbiri kesin değilse **belge aramasına** düşer.

### Onay akışı (yazma işlemleri — human-in-the-loop)
```
"Yarın 15:00 dişçi randevusu ekle"
   → router: calendar + yazma niyeti
   → assistant taslağı çıkarır: {başlık: "Dişçi", başlangıç: yarın 15:00, bitiş: 16:00}
   → arayüz gösterir: "Şu etkinliği ekleyeyim mi? [Onayla / İptal / Düzelt]"
   → Onayla → calendar_tool.create_event(...) → "Eklendi ✓"
   → İptal → hiçbir şey yapılmaz
```
Mail gönderme aynı akış: taslak {kime, konu, gövde} gösterilir → onay → `send_mail`. Kullanıcı "Düzelt" derse taslak güncellenip tekrar onaya sunulur.

---

## 4. Modüller (dizin yapısı)

```
kisisel-asistan/
├── app/
│   ├── config.py         # ayarlar: model adları, yollar, top_k, eşikler
│   ├── llm.py            # Foundry Local sarmalayıcı: chat(), embed()
│   ├── store.py          # SQLite: şema, chunk ekle, hepsini getir
│   ├── ingest.py         # belgeleri oku → parçala → embed → kaydet
│   ├── retriever.py      # sorguyu embed et → cosine top-K parça
│   ├── router.py         # hangi yetenek: documents | calendar | mail | chat
│   ├── assistant.py      # orkestratör: route → bağlam topla → LLM cevabı
│   └── tools/
│       ├── calendar_tool.py  # AppleScript ile Apple Takvim okuma
│       └── mail_tool.py      # AppleScript ile Apple Mail okuma
├── ui/
│   ├── cli.py            # terminal arayüzü (döngüde soru-cevap)
│   └── web.py            # Streamlit sohbet arayüzü
├── data/
│   ├── documents/        # kullanıcının belgeleri buraya konur
│   └── assistant.db      # SQLite veritabanı (çalışınca oluşur)
├── scripts/
│   └── setup_check.py    # foundry/model/python ortam doğrulaması
├── tests/                # birim + entegrasyon testleri
├── requirements.txt
└── README.md
```

### Modül arayüzleri (sözleşmeler)

- **`llm.py`**
  - `chat(system: str, user: str) -> str` — Foundry Local chat completion.
  - `embed(texts: list[str]) -> list[list[float]]` — metinleri vektöre çevirir.
- **`store.py`**
  - `init_db()` ; `add_chunk(source, text, embedding)` ; `all_chunks() -> list[(source, text, embedding)]`.
  - Şema: `chunks(id, source TEXT, text TEXT, embedding BLOB/JSON)`.
- **`ingest.py`**
  - `ingest_folder(path)` — `.txt/.md` (ve mümkünse `.pdf`) oku → parçala → embed → store.
  - Parçalama: paragraf/başlık temelli, ~1–3 paragraf/parça.
- **`retriever.py`**
  - `get_top_chunks(query, k=3) -> list[(source, text, score)]` — sorguyu embed et, tüm vektörlerle cosine benzerlik, en yüksek k.
  - Düşük benzerlik eşiği altında boş dönebilir → "bilgi yok" davranışı.
- **`router.py`**
  - `route(query) -> "documents" | "calendar" | "mail" | "chat"`.
- **`tools/calendar_tool.py`**
  - `get_events(when="today"|"tomorrow"|"week") -> list[Event]` (okuma, AppleScript).
  - `create_event(title, start, end, notes=None) -> bool` (yazma, **yalnızca onay sonrası** çağrılır).
- **`tools/mail_tool.py`**
  - `get_recent(unread_only=False, limit=10, sender=None) -> list[Mail]` (okuma, AppleScript).
  - `send_mail(to, subject, body) -> bool` (yazma, **yalnızca onay sonrası** çağrılır). Seçenek: doğrudan gönder **veya** Mail'de taslak/compose penceresi aç.
- **`assistant.py`**
  - `answer(query) -> Answer{text, sources, pending_action?}` — route → bağlam topla/taslak hazırla → prompt kur → `llm.chat`.
  - Yazma niyeti algılanırsa cevap doğrudan işlem yapmaz; `pending_action` (taslak etkinlik/mail) döndürür. Arayüz bunu gösterip onay ister; onay gelirse `confirm_action(pending_action)` çağrılır.

---

## 5. Veri akışı (belge sorusu örneği)

1. Kullanıcı soru sorar (CLI/Web).
2. `router.route(q)` → `"documents"`.
3. `retriever.get_top_chunks(q, k=3)` → en ilgili parçalar (+ kaynak adları).
4. `assistant` promptu kurar: sistem talimatı ("yalnızca verilen bağlamı kullan; yoksa bilmiyorum de; kaynak belirt") + parçalar + soru.
5. `llm.chat(...)` (Foundry Local) → cevap.
6. Cevap + kaynaklar gösterilir.

Takvim/mail akışları aynı iskelet; 3. adımda ilgili araç çağrılır.

---

## 6. Hata yönetimi

Tümü kullanıcıya **anlaşılır Türkçe** mesaj verir, çökmez:

- Foundry Local servisi kapalı/erişilemiyor → nasıl başlatılacağını söyle.
- Model inmemiş → indirme talimatı (veya otomatik indirme denemesi).
- `data/documents/` boş / ingest yapılmamış → belge ekleyip ingest çalıştır uyarısı.
- Retrieval eşik altı (ilgili parça yok) → "Belgelerimde bu konuda bilgi yok."
- AppleScript izni reddedildi → System Settings > Privacy & Security > Automation'dan izin ver açıklaması.
- Mail/Takvim hesabı yok/boş → "Hesap bulunamadı / etkinlik yok."
- Model yavaş/timeout → makul timeout + bekleme göstergesi.
- **Yazma işlemi (ekle/gönder) onaysız asla çalışmaz.** Taslak eksik/anlaşılmazsa (ör. mail adresi yok) işlem yapılmaz, kullanıcıdan bilgi istenir.
- Yazma AppleScript hatası (gönderilemedi/eklenemedi) → net hata mesajı, işlem yapılmadı bildirimi.

---

## 7. Test stratejisi

**Deterministik parçalar — birim testi (asserts):**
- `ingest`: parçalama doğru sayıda/temiz parça üretir.
- `retriever`: bilinen küçük veri kümesinde cosine sıralaması beklendiği gibi.
- `router`: anahtar kelime kuralları doğru etiket döndürür.
- `store`: ekle/getir tutarlı.

**LLM'e bağlı parçalar (deterministik değil):**
- Doğru bağlamın (parça/etkinlik/mail) toplandığı doğrulanır.
- Cevabın boş olmadığı ve kaynak alanının dolduğu kontrol edilir.
- "Cevaplanamaz" soruda fallback mesajının çıktığı test edilir.

**Elle test seti:**
- Belgeden cevaplanabilir + cevaplanamaz sorular.
- "Bugün takvimimde ne var?" / "Okunmamış maillerim neler?" doğru araca gidiyor mu.
- Uç durumlar: boş sorgu, çok genel soru.

---

## 8. Kurulum adımları (özet)

1. Homebrew kur → `brew install foundrylocal`.
2. `foundry model list` → uygun küçük chat + embedding modelini seç/indir.
3. Python venv (önce 3.14; sorun olursa 3.12) → `pip install -r requirements.txt`.
4. `data/documents/` içine başlangıç belgeleri koy → `python -m app.ingest`.
5. `scripts/setup_check.py` ile ortamı doğrula.
6. Kullan: `python -m ui.cli` veya `streamlit run ui/web.py`.

---

## 9. Kapsam dışı (YAGNI)

- Onaysız/otomatik yazma; toplu silme; etkinlik veya mail **silme**.
- Bulut/Azure model, çevrimiçi arama.
- Büyük vektör veritabanları (Chroma/FAISS vb.) — küçük veri için gereksiz; SQLite + bellek-içi cosine yeterli.
- Çok-turlu karmaşık agent zincirleri; basit tek-adım araç seçimi yeterli.
- Kimlik doğrulama, çok kullanıcılı destek, dağıtım/paketleme.

---

## 10. Başarı ölçütü

- `data/documents/` içindeki belgeler hakkında sorulara kaynak göstererek doğru cevap verir; bilmediğinde "bilmiyorum" der.
- "Bugün ne var?" → Apple Takvim'den doğru etkinlikleri özetler.
- "Okunmamış maillerim?" → Apple Mail'den doğru e-postaları özetler.
- "Yarın 15:00 dişçi randevusu ekle" → taslak gösterir, **onay sonrası** etkinliği ekler.
- "X'e şu maili gönder" → taslak gösterir, **onay sonrası** e-postayı gönderir; onaysız asla göndermez.
- Tümü internetsiz (mail/takvim dahil, yerel Apple uygulamaları), Mac'te, makul sürede (~birkaç saniye) çalışır.
- Hem CLI hem Streamlit arayüzünden kullanılabilir.
- Kod GitHub'da bir repoda sürüm kontrollü tutulur.
