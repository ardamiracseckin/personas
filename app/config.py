from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "assistant.db"

# Foundry Local chat model (verified via `foundry model list`).
CHAT_MODEL = "phi-3.5-mini"

# Embedding model — Foundry Local's catalog had no embedding model, so we use a
# small multilingual model via fastembed (ONNX, CPU-friendly, good Turkish support).
EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Retrieval tunables
TOP_K = 3
SIM_THRESHOLD = 0.20  # cosine below this ⇒ treat as "no relevant info"

# Chunking
MAX_CHUNK_CHARS = 800
