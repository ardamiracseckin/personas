from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "assistant.db"

# Foundry Local chat model (verified via `foundry model list`).
# qwen2.5-1.5b: küçük ama phi-3.5-mini'den belirgin daha iyi Türkçe; 8 GB RAM'e uygun.
CHAT_MODEL = "qwen2.5-1.5b"

# Embedding model — Foundry Local's catalog had no embedding model, so we use a
# small multilingual model via fastembed (ONNX, CPU-friendly, good Turkish support).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Retrieval tunables — eval/questions.json üzerinde ölçülerek seçildi
# (bkz. docs/eval/degerlendirme-raporu.md). TOP_K=1 iken isabet 13/14, K>=2 iken 14/14;
# K=3 marj bırakır. Eşik 0.40: cevaplanabilirlerin en düşük skoru 0.43,
# cevaplanamazların en yükseği 0.44 olduğu için kusursuz ayıran eşik yok —
# 0.40 erişimi tam tutar, kalan sızıntıyı istemdeki "bilmiyorum" kuralı karşılar.
TOP_K = 3
SIM_THRESHOLD = 0.40  # cosine below this ⇒ treat as "no relevant info"

# Chunking
# Parçalama başlık sınırlarında bölündüğü için bu üst sınır nadiren devreye girer:
# 8 belgelik bilgi tabanında 58 parça, ortalama 433 karakter (~1-3 paragraf).
MAX_CHUNK_CHARS = 800
