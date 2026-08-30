from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "assistant.db"

# Foundry Local chat model (verified via `foundry model list`).
# Dört aday aynı soru setiyle ölçüldü (bkz. docs/eval/degerlendirme-raporu.md §5):
# phi-4-mini kalitede açık ara önde (22/28), qwen2.5-1.5b daha hızlı (p50 2.45 sn'ye karşı
# 3.95 sn) ama iki ağır hata yapıyor. Doğruluk, hız yerine tercih edildi.
# Daha hafif alternatif: CHAT_MODEL = "qwen2.5-1.5b" (1.5 GB, p50 2.45 sn).
CHAT_MODEL = "phi-4-mini"

# Arayüzden seçilebilen modeller. 8 GB bellekte aynı anda yalnızca biri yüklü
# durur; geçiş app/models.py üzerinden yapılır ve ~20-30 saniye sürer.
MODEL_CATALOG = [
    {"alias": "phi-4-mini", "boyut": "3.7 GB", "gorsel": False,
     "not": "En doğru cevaplar (varsayılan)"},
    {"alias": "qwen2.5-1.5b", "boyut": "1.5 GB", "gorsel": False,
     "not": "En hızlı, hafif donanım için"},
    # Görsel-dil modeli, ama Foundry Local'in OpenAI uç noktası içerik dizisini
    # metne çevirip görseli modele iletmiyor (0.10.3'te doğrulandı). Sohbet için
    # kullanılabilir; görsel yeteneği bu yüzden kapalı işaretli.
    {"alias": "qwen3-vl-2b-instruct", "boyut": "1.3 GB", "gorsel": False,
     "not": "En hafif model; görsel yeteneği Foundry tarafından iletilmiyor"},
]

# Üretilecek en fazla belirteç. Ölçüm: doğru cevaplar 200-600 karakter (~60-200
# belirteç) sürüyor; sınır 1200 iken model belirsiz sorularda 4000+ karakter
# yazıp yanıtı 48 saniyeye çıkarıyordu. 450 normal cevaba fazlasıyla yeter,
# savrulmayı keser.
MAX_TOKENS = 450

# WhatsApp gönderimi: varsayılan olarak taslak açılır ve gönder tuşuna kullanıcı
# basar. True yapılırsa asistan onaydan sonra Enter'a da basar; bu macOS
# Erişilebilirlik izni ister ve WhatsApp arayüzü değişirse bozulabilir.
WHATSAPP_AUTO_SEND = False
DEFAULT_COUNTRY_CODE = "90"

# Not: 0.8 sürümünde yüklü model 600 sn hareketsizlikte bellekten atılıyor ve ilk
# soru ~30 saniye sürüyordu. 0.10 ile bu davranış Foundry ayarına taşındı
# (`foundry config show` → idle-timeout-minutes, varsayılan: disabled), bu yüzden
# uygulama tarafında TTL ayarı tutulmuyor. Sunucu açılışında model yine de ısıtılır.

# Embedding model — Foundry Local's catalog had no embedding model, so we use a
# small multilingual model via fastembed (ONNX, CPU-friendly, good Turkish support).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Retrieval tunables — eval/questions.json üzerinde ölçülerek seçildi
# (bkz. docs/eval/degerlendirme-raporu.md). TOP_K=1 iken isabet 13/14, K>=2 iken 14/14;
# K=3 marj bırakır. Eşik hibrit skora göre yeniden tarandı; 0.34 üç ölçütte birden
# en iyisi: temiz sorularda isabet 14/14, yazım hatalı sorularda 13/14,
# cevaplanamazlarda çekimserlik 6/6. Yalnız kosinüsle en iyi sonuç 14/12/5'ti.
TOP_K = 3

# Hibrit erişim ağırlıkları: kosinüs anlamı, sözlüksel katman yazım hatasını yakalar
# (bkz. app/lexical.py). Skor = DENSE_WEIGHT x kosinüs + LEXICAL_WEIGHT x sözlüksel.
DENSE_WEIGHT = 0.75
LEXICAL_WEIGHT = 0.25

# Kısa/anahtar kelime sorgularında ("git stash ne işe yarar?") embedding skoru
# düşük kalıyor ve harmanlanmış skor eşiğin altına düşüyordu. Kelimelerin yarısı
# birebir tutuyorsa ve anlamsal yakınlık tabanın üstündeyse parça yine kabul edilir.
LEXICAL_RESCUE = 0.5
# Mevzuat korpusuyla ölçülerek yükseltildi (eskiden 0.10). Bulanık kurtarma
# kuralı yazım hatalı soruları kurtarmak içindir; yazım hatalı bir soru yine de
# makul bir kosinüs verir. 0.10 tabanıyla "Bugün hava nasıl olacak?" gibi
# sorular kanun metnine bağlanıyordu: yaygın kelimeler ("nasıl", "olacak") uzun
# maddelerde bulunduğu için bulanık skor 0,75'e çıkıyor, kosinüs ise 0,14'te
# kalıyordu. Taban 0.30'a çekilince alakasız sorularda çekimserlik 2/6'dan
# 6/6'ya çıktı, erişim isabetinden kayıp olmadı.
DENSE_FLOOR = 0.30
# Mevzuat korpusunda taramayla seçildi. 0.30-0.42 aralığı erişim isabetini
# değiştirmiyor (4/4/5); 0.38 ise sınırda kalan alakasız soruyu da eliyor.
SIM_THRESHOLD = 0.38  # hibrit skor bunun altındaysa ⇒ "ilgili bilgi yok"

# Chunking
# Parçalama başlık sınırlarında bölündüğü için bu üst sınır nadiren devreye girer:
# 8 belgelik bilgi tabanında 58 parça, ortalama 433 karakter (~1-3 paragraf).
MAX_CHUNK_CHARS = 800
