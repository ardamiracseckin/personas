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
    {"alias": "qwen3-vl-2b-instruct", "boyut": "1.3 GB", "gorsel": True,
     "not": "Görsel yükleyip soru sorabilirsin"},
]

# Üretilecek en fazla belirteç. Sınırsız bırakıldığında model bazen sayfalarca
# yazıyor; 1200 belirteç uzun bir kod örneği + açıklamaya rahat yetiyor.
MAX_TOKENS = 1200

# Embedding model — Foundry Local's catalog had no embedding model, so we use a
# small multilingual model via fastembed (ONNX, CPU-friendly, good Turkish support).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Retrieval tunables — eval/questions.json üzerinde ölçülerek seçildi
# (bkz. docs/eval/degerlendirme-raporu.md). TOP_K=1 iken isabet 13/14, K>=2 iken 14/14;
# K=3 marj bırakır. Eşik 0.40: cevaplanabilirlerin en düşük skoru 0.43,
# cevaplanamazların en yükseği 0.44 olduğu için kusursuz ayıran eşik yok —
# 0.40 erişimi tam tutar, kalan sızıntıyı istemdeki "bilmiyorum" kuralı karşılar.
TOP_K = 3

# Hibrit erişim ağırlıkları: kosinüs anlamı, sözlüksel katman yazım hatasını yakalar
# (bkz. app/lexical.py). Skor = DENSE_WEIGHT x kosinüs + LEXICAL_WEIGHT x sözlüksel.
DENSE_WEIGHT = 0.75
LEXICAL_WEIGHT = 0.25
SIM_THRESHOLD = 0.40  # cosine below this ⇒ treat as "no relevant info"

# Chunking
# Parçalama başlık sınırlarında bölündüğü için bu üst sınır nadiren devreye girer:
# 8 belgelik bilgi tabanında 58 parça, ortalama 433 karakter (~1-3 paragraf).
MAX_CHUNK_CHARS = 800
