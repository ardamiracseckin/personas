# personas — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `personas`, an offline-first personal assistant on macOS that answers questions from the user's own documents (local RAG via Microsoft Foundry Local), and reads/writes Apple Calendar & Apple Mail with human-in-the-loop confirmation.

**Architecture:** A small local LLM (Foundry Local) is the "brain". A router classifies each query (documents / calendar / mail / chat) and detects read vs write intent. Read queries gather context (RAG chunks from SQLite, or Calendar/Mail via AppleScript) and the LLM answers. Write intents (create event / send mail) produce a *draft* that the user must explicitly confirm before it executes. Two thin frontends (CLI + Streamlit) share one orchestrator.

**Tech Stack:** Python 3.12 (fallback from 3.14 if wheels missing), Foundry Local + `foundry-local-sdk` + `openai` client, SQLite (`sqlite3` stdlib), `numpy`, Streamlit, AppleScript via `osascript` (subprocess), `pytest`, git + GitHub (`gh`).

## Global Constraints

- **Offline only.** No cloud/Azure/API calls. All inference via Foundry Local on-device. (Mail/Calendar are local Apple apps.)
- **Hardware:** Apple M2, 8 GB RAM → only small models; load at most one chat model + one small embedding model.
- **Python:** target 3.12 venv (system has 3.14; fall back if any dependency lacks 3.14 wheels).
- **Write actions require explicit user confirmation.** `create_event` / `send_mail` are NEVER called without a confirmation step. No deleting anything, ever.
- **Language:** all user-facing strings in Turkish.
- **Model aliases are placeholders** until verified with `foundry model list` in Task 1; update `app/config.py` with the real ids there.
- **Repo:** private GitHub repo `personas` under user `ardamiracseckin`. Commit after every task.
- **Project root:** `MICROSFT PROJE RAG/personas` (all paths below are relative to it).

---

## File Structure

```
personas/
├── app/
│   ├── __init__.py
│   ├── config.py            # paths, model aliases, tunables
│   ├── store.py             # SQLite: schema + CRUD for chunks
│   ├── chunking.py          # pure text-splitting helpers
│   ├── similarity.py        # pure cosine similarity
│   ├── llm.py               # Foundry Local wrapper: chat(), embed()
│   ├── ingest.py            # documents → chunks → embeddings → store
│   ├── retriever.py         # query → top-K chunks
│   ├── router.py            # classify query: tool + read/write intent
│   ├── assistant.py         # orchestrator: route → context/draft → answer
│   └── tools/
│       ├── __init__.py
│       ├── applescript.py   # run_osascript() helper + errors
│       ├── calendar_tool.py # read events + create_event (confirmed)
│       └── mail_tool.py     # read mail + send_mail (confirmed)
├── ui/
│   ├── __init__.py
│   ├── cli.py               # terminal chat loop w/ confirmation
│   └── web.py               # Streamlit chat w/ confirmation buttons
├── data/
│   ├── documents/           # user drops .txt/.md here (seed samples added)
│   └── assistant.db         # created at runtime (gitignored)
├── scripts/
│   └── setup_check.py       # verify foundry, models, python, permissions
├── tests/
│   ├── test_store.py
│   ├── test_chunking.py
│   ├── test_similarity.py
│   ├── test_retriever.py
│   ├── test_router.py
│   ├── test_assistant.py
│   ├── test_calendar_tool.py
│   └── test_mail_tool.py
├── docs/                    # spec + this plan
├── requirements.txt
├── .gitignore
└── README.md
```

**Build order rationale:** Phase 0 sets up the environment + repo (needs the user's machine). Phases 1–2 build pure, fully-testable core (store, chunking, similarity) with no Foundry dependency. Phase 3 wires the Foundry LLM. Phases 4–6 add RAG, routing, tools. Phase 7 adds confirmed write actions. Phase 8 adds the two UIs. Phase 9 finalizes docs/seed data.

---

## Phase 0 — Environment, scaffolding & GitHub (guided, with the user)

### Task 0.1: Homebrew + Foundry Local + models

Environment prep. No automated test — verified by the model listing.

- [ ] **Step 1: Install Homebrew** (user runs; needs admin password)

Run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Then add to PATH (Apple Silicon):
```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```
Expected: `brew --version` prints a version.

- [ ] **Step 2: Install Foundry Local**

Run: `brew install microsoft/foundrylocal/foundrylocal`
Expected: `foundry --version` prints a version. If the tap name differs, consult https://learn.microsoft.com/azure/ai-foundry/foundry-local/get-started .

- [ ] **Step 3: List available models and pick real aliases**

Run: `foundry model list`
Expected: a catalog table. Record:
- a small **chat** model alias (e.g. `phi-3.5-mini-instruct` or the smallest instruct model shown),
- a small **embedding** model alias (e.g. `qwen3-embedding-0.6b` if present).

Write these two exact aliases down; they go into `app/config.py` in Task 1. **If no embedding model is listed**, mark that fact — Task 3 will use the `sentence-transformers` fallback instead.

- [ ] **Step 4: Warm the chat model once**

Run: `foundry model run <chat-alias>` then type a short prompt, confirm a reply, exit.
Expected: a coherent completion, proving the runtime works on this machine.

### Task 0.2: Python venv + project skeleton + git

- [ ] **Step 1: Create the venv** (try 3.14, fall back to 3.12)

Run:
```bash
cd "MICROSFT PROJE RAG/personas"
python3 -m venv .venv && source .venv/bin/activate
python -V
```
If a later `pip install` fails on 3.14 wheels, recreate with 3.12:
```bash
brew install python@3.12
/opt/homebrew/bin/python3.12 -m venv .venv && source .venv/bin/activate
```

- [ ] **Step 2: Write `requirements.txt`**

```
foundry-local-sdk
openai
numpy
streamlit
pytest
```
(Add `sentence-transformers` here only if Task 0.1 Step 3 found no embedding model.)

- [ ] **Step 3: Install deps**

Run: `pip install -r requirements.txt`
Expected: completes without error. (If it fails on Python 3.14, do Step 1's 3.12 fallback, then re-run.)

- [ ] **Step 4: Create package skeleton + `.gitignore`**

Create empty `app/__init__.py`, `app/tools/__init__.py`, `ui/__init__.py`, and `data/documents/.gitkeep`.

`.gitignore`:
```
.venv/
__pycache__/
*.pyc
data/assistant.db
.DS_Store
```

- [ ] **Step 5: Init git and first commit**

Run:
```bash
git init
git add .
git commit -m "chore: project skeleton, requirements, gitignore"
```

### Task 0.3: Install `gh` and create the private GitHub repo

- [ ] **Step 1: Install GitHub CLI**

Run: `brew install gh`
Expected: `gh --version` prints a version.

- [ ] **Step 2: Authenticate (USER ACTION — browser login)**

Run: `gh auth login`
Choose: GitHub.com → HTTPS → "Login with a web browser" → copy the one-time code → authorize in browser.
Expected: `gh auth status` shows logged in as `ardamiracseckin`.

- [ ] **Step 3: Create the private repo and push**

Run:
```bash
gh repo create personas --private --source=. --remote=origin --push
```
Expected: repo created at `https://github.com/ardamiracseckin/personas`, initial commit pushed.

---

## Phase 1 — Config & storage (pure, fully testable, no Foundry)

### Task 1: `app/config.py`

**Files:**
- Create: `app/config.py`

**Interfaces:**
- Produces: `BASE_DIR`, `DATA_DIR: Path`, `DOCUMENTS_DIR: Path`, `DB_PATH: Path`, `CHAT_MODEL: str`, `EMBED_MODEL: str | None`, `TOP_K: int`, `SIM_THRESHOLD: float`, `MAX_CHUNK_CHARS: int`.

- [ ] **Step 1: Write `app/config.py`**

```python
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
DB_PATH = DATA_DIR / "assistant.db"

# Foundry Local aliases — REPLACE with the exact ids from `foundry model list` (Task 0.1).
CHAT_MODEL = "phi-3.5-mini-instruct"
EMBED_MODEL = "qwen3-embedding-0.6b"  # set to None if no embedding model → sentence-transformers fallback

# Retrieval tunables
TOP_K = 3
SIM_THRESHOLD = 0.20  # cosine below this ⇒ treat as "no relevant info"

# Chunking
MAX_CHUNK_CHARS = 800
```

- [ ] **Step 2: Commit**

```bash
git add app/config.py && git commit -m "feat: app config (paths, model aliases, tunables)"
```

### Task 2: `app/store.py` (SQLite CRUD)

**Files:**
- Create: `app/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Produces: `init_db()`, `clear()`, `add_chunk(source: str, text: str, embedding: list[float])`, `all_chunks() -> list[tuple[str, str, list[float]]]`, `count() -> int`. All operate on `config.DB_PATH`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_store.py
import app.config as config
from app import store

def test_add_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    store.init_db()
    assert store.count() == 0
    store.add_chunk("doc1.md", "hello world", [0.1, 0.2, 0.3])
    assert store.count() == 1
    rows = store.all_chunks()
    assert rows == [("doc1.md", "hello world", [0.1, 0.2, 0.3])]
    store.clear()
    assert store.count() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_store.py -v`
Expected: FAIL (`ModuleNotFoundError: app.store` or `AttributeError`).

- [ ] **Step 3: Write minimal implementation**

```python
# app/store.py
import json
import sqlite3
from app import config


def _conn():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "source TEXT NOT NULL, text TEXT NOT NULL, embedding TEXT NOT NULL)"
        )


def clear():
    with _conn() as c:
        c.execute("DELETE FROM chunks")


def add_chunk(source, text, embedding):
    with _conn() as c:
        c.execute(
            "INSERT INTO chunks(source, text, embedding) VALUES (?, ?, ?)",
            (source, text, json.dumps(embedding)),
        )


def all_chunks():
    with _conn() as c:
        rows = c.execute("SELECT source, text, embedding FROM chunks").fetchall()
    return [(s, t, json.loads(e)) for (s, t, e) in rows]


def count():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_store.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/store.py tests/test_store.py && git commit -m "feat: SQLite chunk store with tests"
```

---

## Phase 2 — Pure RAG helpers (fully testable, no Foundry)

### Task 3: `app/chunking.py`

**Files:**
- Create: `app/chunking.py`
- Test: `tests/test_chunking.py`

**Interfaces:**
- Produces: `chunk_text(text: str, max_chars: int = 800) -> list[str]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chunking.py
from app.chunking import chunk_text

def test_splits_on_blank_lines_and_packs():
    text = "Para one.\n\nPara two.\n\nPara three."
    chunks = chunk_text(text, max_chars=20)
    assert chunks == ["Para one.", "Para two.", "Para three."]

def test_packs_small_paras_together():
    text = "aa\n\nbb\n\ncc"
    assert chunk_text(text, max_chars=100) == ["aa\n\nbb\n\ncc"]

def test_ignores_empty_input():
    assert chunk_text("   \n\n  ") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_chunking.py -v`
Expected: FAIL (`ModuleNotFoundError`).

- [ ] **Step 3: Write minimal implementation**

```python
# app/chunking.py
def chunk_text(text, max_chars=800):
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        if cur and len(cur) + len(p) + 2 > max_chars:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_chunking.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/chunking.py tests/test_chunking.py && git commit -m "feat: paragraph chunker with tests"
```

### Task 4: `app/similarity.py`

**Files:**
- Create: `app/similarity.py`
- Test: `tests/test_similarity.py`

**Interfaces:**
- Produces: `cosine(a: list[float], b: list[float]) -> float`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_similarity.py
from app.similarity import cosine

def test_identical_vectors():
    assert cosine([1, 0], [1, 0]) == 1.0

def test_orthogonal_vectors():
    assert cosine([1, 0], [0, 1]) == 0.0

def test_zero_vector_is_safe():
    assert cosine([0, 0], [1, 1]) == 0.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_similarity.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/similarity.py
import math

def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_similarity.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/similarity.py tests/test_similarity.py && git commit -m "feat: cosine similarity with tests"
```

---

## Phase 3 — Foundry Local LLM wrapper

### Task 5: `app/llm.py`

**Files:**
- Create: `app/llm.py`
- Test: `tests/test_llm.py` (unit test with a fake client; no live model needed)

**Interfaces:**
- Consumes: `config.CHAT_MODEL`, `config.EMBED_MODEL`.
- Produces: `chat(system: str, user: str) -> str`, `embed(texts: list[str]) -> list[list[float]]`. Internally lazy-inits a Foundry Local manager + OpenAI-compatible client.

**Note:** The Foundry Local SDK surface must be confirmed against the installed version's docs (`https://learn.microsoft.com/azure/ai-foundry/foundry-local/`). The code below follows the documented `FoundryLocalManager` + `openai` pattern. Keep the network/model calls isolated in `_client()` so the pure logic stays testable.

- [ ] **Step 1: Write the failing test (fake client injection)**

```python
# tests/test_llm.py
from app import llm

class _FakeMsg:  # minimal shape of openai response
    def __init__(self, content): self.message = type("M", (), {"content": content})
class _FakeChat:
    def __init__(self): self.completions = self
    def create(self, **kw): 
        self.kw = kw
        return type("R", (), {"choices": [_FakeMsg("cevap")]})
class _FakeEmb:
    def create(self, **kw):
        return type("R", (), {"data": [type("D", (), {"embedding": [0.1, 0.2]})()
                                        for _ in kw["input"]]})
class _FakeClient:
    def __init__(self): self.chat = _FakeChat(); self.embeddings = _FakeEmb()

def test_chat_returns_content(monkeypatch):
    monkeypatch.setattr(llm, "_client", lambda: (_FakeClient(), "model-id"))
    assert llm.chat("sys", "soru") == "cevap"

def test_embed_returns_vectors(monkeypatch):
    monkeypatch.setattr(llm, "_client", lambda: (_FakeClient(), "model-id"))
    monkeypatch.setattr(llm, "_embed_model_id", lambda: "emb-id")
    assert llm.embed(["a", "b"]) == [[0.1, 0.2], [0.1, 0.2]]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_llm.py -v`
Expected: FAIL (`AttributeError: module 'app.llm' has no attribute '_client'`).

- [ ] **Step 3: Write minimal implementation**

```python
# app/llm.py
from app import config

_manager = None
_openai = None

def _client():
    """Lazy-init Foundry Local manager + OpenAI-compatible client. Returns (client, chat_model_id)."""
    global _manager, _openai
    if _openai is None:
        from foundry_local import FoundryLocalManager
        from openai import OpenAI
        _manager = FoundryLocalManager(config.CHAT_MODEL)
        _openai = OpenAI(base_url=_manager.endpoint, api_key=_manager.api_key or "not-needed")
    chat_id = _manager.get_model_info(config.CHAT_MODEL).id
    return _openai, chat_id

def _embed_model_id():
    # Ensures the embedding model is registered with the running manager.
    _client()
    return _manager.get_model_info(config.EMBED_MODEL).id

def chat(system, user):
    client, model_id = _client()
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

def embed(texts):
    client, _ = _client()
    resp = client.embeddings.create(model=_embed_model_id(), input=list(texts))
    return [d.embedding for d in resp.data]
```

**If Task 0.1 found no embedding model:** replace `embed()` with a `sentence-transformers` version:
```python
_st_model = None
def embed(texts):
    global _st_model
    if _st_model is None:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _st_model.encode(list(texts)).tolist()
```
and delete `_embed_model_id`; the test for `embed` then needs the fake swapped for a fake `_st_model` instead — adjust accordingly.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_llm.py -v`
Expected: PASS.

- [ ] **Step 5: Live smoke test (manual, needs Foundry running)**

Run: `python -c "from app import llm; print(llm.chat('Kısa cevap ver.', 'Merhaba!')); print(len(llm.embed(['deneme'])[0]))"`
Expected: a short Turkish reply, then an integer embedding dimension. If it errors, re-check model aliases in `config.py` against `foundry model list`.

- [ ] **Step 6: Commit**

```bash
git add app/llm.py tests/test_llm.py && git commit -m "feat: Foundry Local chat+embed wrapper with unit tests"
```

---

## Phase 4 — Ingestion & retrieval

### Task 6: `app/ingest.py`

**Files:**
- Create: `app/ingest.py`
- Test: `tests/test_ingest.py`

**Interfaces:**
- Consumes: `chunking.chunk_text`, `llm.embed`, `store.*`, `config.DOCUMENTS_DIR`.
- Produces: `ingest_folder(folder: Path | None = None, embed_fn=llm.embed) -> int` (returns number of chunks stored). Reads `*.txt` and `*.md`. `embed_fn` is injectable for testing.

- [ ] **Step 1: Write the failing test (inject fake embed)**

```python
# tests/test_ingest.py
import app.config as config
from app import ingest, store

def fake_embed(texts):
    return [[float(len(t)), 0.0] for t in texts]

def test_ingest_reads_files_and_stores_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    docs = tmp_path / "docs"; docs.mkdir()
    (docs / "a.md").write_text("Bir.\n\nİki.")
    (docs / "b.txt").write_text("Üç.")
    store.init_db(); store.clear()
    n = ingest.ingest_folder(docs, embed_fn=fake_embed)
    assert n == 3
    assert store.count() == 3
    sources = {s for (s, _t, _e) in store.all_chunks()}
    assert sources == {"a.md", "b.txt"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_ingest.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/ingest.py
from pathlib import Path
from app import config, chunking, store, llm

def ingest_folder(folder=None, embed_fn=None):
    folder = Path(folder) if folder else config.DOCUMENTS_DIR
    embed_fn = embed_fn or llm.embed
    store.init_db()
    store.clear()
    total = 0
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in (".txt", ".md"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunking.chunk_text(text, config.MAX_CHUNK_CHARS)
        if not chunks:
            continue
        vectors = embed_fn(chunks)
        for chunk, vec in zip(chunks, vectors):
            store.add_chunk(path.name, chunk, vec)
            total += 1
    return total
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_ingest.py -v`
Expected: PASS.

- [ ] **Step 5: Add a runnable entrypoint + commit**

Append to `app/ingest.py`:
```python
if __name__ == "__main__":
    n = ingest_folder()
    print(f"{n} parça veritabanına eklendi.")
```
```bash
git add app/ingest.py tests/test_ingest.py && git commit -m "feat: document ingestion pipeline with tests"
```

### Task 7: `app/retriever.py`

**Files:**
- Create: `app/retriever.py`
- Test: `tests/test_retriever.py`

**Interfaces:**
- Consumes: `store.all_chunks`, `similarity.cosine`, `llm.embed`, `config.TOP_K`, `config.SIM_THRESHOLD`.
- Produces: `get_top_chunks(query: str, k: int | None = None, embed_fn=None) -> list[tuple[str, str, float]]` — `(source, text, score)` sorted by score desc, filtered by `SIM_THRESHOLD`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_retriever.py
import app.config as config
from app import retriever, store

def test_returns_most_similar_above_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db(); store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    store.add_chunk("d", "köpekler", [0.0, 1.0])
    res = retriever.get_top_chunks("q", k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert res[0][1] == "kediler"
    assert res[0][2] > 0.99

def test_threshold_filters_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.99)
    store.init_db(); store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    res = retriever.get_top_chunks("q", embed_fn=lambda t: [[0.0, 1.0]])
    assert res == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_retriever.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/retriever.py
from app import config, store, llm
from app.similarity import cosine

def get_top_chunks(query, k=None, embed_fn=None):
    k = k or config.TOP_K
    embed_fn = embed_fn or llm.embed
    qvec = embed_fn([query])[0]
    scored = [(src, txt, cosine(qvec, emb)) for (src, txt, emb) in store.all_chunks()]
    scored = [row for row in scored if row[2] >= config.SIM_THRESHOLD]
    scored.sort(key=lambda r: r[2], reverse=True)
    return scored[:k]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_retriever.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/retriever.py tests/test_retriever.py && git commit -m "feat: top-K retriever with threshold and tests"
```

---

## Phase 5 — Router

### Task 8: `app/router.py`

**Files:**
- Create: `app/router.py`
- Test: `tests/test_router.py`

**Interfaces:**
- Produces: `route(query: str) -> dict` with keys `tool` ∈ `{"documents","calendar","mail","chat"}` and `action` ∈ `{"read","write"}`. Rule-first (keyword) classification; defaults to `{"documents","read"}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_router.py
from app.router import route

def test_calendar_read():
    assert route("Bugün takvimimde ne var?") == {"tool": "calendar", "action": "read"}

def test_calendar_write():
    assert route("Yarın 15:00 dişçi randevusu ekle") == {"tool": "calendar", "action": "write"}

def test_mail_read():
    assert route("Okunmamış maillerim neler?") == {"tool": "mail", "action": "read"}

def test_mail_write():
    assert route("Ahmet'e bir mail gönder") == {"tool": "mail", "action": "write"}

def test_defaults_to_documents():
    assert route("Kireç temizliği nasıl yapılır?") == {"tool": "documents", "action": "read"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_router.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/router.py
CAL_WORDS = ("takvim", "etkinlik", "toplantı", "randevu", "bugün ne", "yarın", "ajanda")
MAIL_WORDS = ("mail", "e-posta", "eposta", "gelen kutusu", "okunmamış", "mesaj")
WRITE_WORDS = ("ekle", "oluştur", "kur", "ayarla", "gönder", "yolla", "ilet", "at ")

def route(query):
    q = query.lower()
    is_write = any(w in q for w in WRITE_WORDS)
    if any(w in q for w in CAL_WORDS):
        return {"tool": "calendar", "action": "write" if is_write else "read"}
    if any(w in q for w in MAIL_WORDS):
        return {"tool": "mail", "action": "write" if is_write else "read"}
    return {"tool": "documents", "action": "read"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_router.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/router.py tests/test_router.py && git commit -m "feat: keyword router (tool + read/write intent) with tests"
```

---

## Phase 6 — Apple tools (read)

### Task 9: `app/tools/applescript.py` helper

**Files:**
- Create: `app/tools/applescript.py`
- Test: `tests/test_applescript.py`

**Interfaces:**
- Produces: `run(script: str, timeout: int = 20) -> str` (raises `AppleScriptError` with a Turkish message on failure/permission denial).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_applescript.py
import subprocess
import pytest
from app.tools import applescript

def test_run_returns_stdout(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="merhaba\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert applescript.run('return "x"') == "merhaba"

def test_run_raises_turkish_on_error(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not authorized")
    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(applescript.AppleScriptError) as e:
        applescript.run("bad")
    assert "izin" in str(e.value).lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_applescript.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/tools/applescript.py
import subprocess

class AppleScriptError(Exception):
    pass

def run(script, timeout=20):
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise AppleScriptError("İşlem zaman aşımına uğradı (uygulama yanıt vermedi).")
    if proc.returncode != 0:
        err = (proc.stderr or "").lower()
        if "not authorized" in err or "authoriz" in err or "-1743" in err:
            raise AppleScriptError(
                "İzin gerekli: System Settings > Privacy & Security > Automation'dan "
                "Terminal'e Mail/Takvim erişimi verin."
            )
        raise AppleScriptError(f"AppleScript hatası: {proc.stderr.strip()}")
    return proc.stdout.strip()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_applescript.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/tools/applescript.py tests/test_applescript.py && git commit -m "feat: osascript helper with Turkish permission errors"
```

### Task 10: `app/tools/calendar_tool.py` (read events)

**Files:**
- Create: `app/tools/calendar_tool.py`
- Test: `tests/test_calendar_tool.py`

**Interfaces:**
- Consumes: `applescript.run`.
- Produces: `parse_events(raw: str) -> list[dict]` (pure; each `{"title","start"}`), and `get_events(when="today", run_fn=applescript.run) -> list[dict]`. `create_event(...)` is added in Task 13.

- [ ] **Step 1: Write the failing test (pure parser + injected run)**

```python
# tests/test_calendar_tool.py
from app.tools import calendar_tool

def test_parse_events():
    raw = "Toplantı|2026-07-03 10:00\nDişçi|2026-07-04 15:00"
    assert calendar_tool.parse_events(raw) == [
        {"title": "Toplantı", "start": "2026-07-03 10:00"},
        {"title": "Dişçi", "start": "2026-07-04 15:00"},
    ]

def test_parse_empty():
    assert calendar_tool.parse_events("") == []

def test_get_events_uses_run_fn():
    out = calendar_tool.get_events(run_fn=lambda script: "X|2026-07-03 09:00")
    assert out == [{"title": "X", "start": "2026-07-03 09:00"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_calendar_tool.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/tools/calendar_tool.py
from app.tools import applescript

_READ_TODAY = '''
set output to ""
set startDate to current date
set hours of startDate to 0
set minutes of startDate to 0
set seconds of startDate to 0
set endDate to startDate + (1 * days)
tell application "Calendar"
  repeat with cal in calendars
    repeat with ev in (every event of cal whose start date >= startDate and start date < endDate)
      set output to output & (summary of ev) & "|" & (start date of ev as string) & linefeed
    end repeat
  end repeat
end tell
return output
'''

def parse_events(raw):
    events = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        title, start = line.split("|", 1)
        events.append({"title": title.strip(), "start": start.strip()})
    return events

def get_events(when="today", run_fn=None):
    run_fn = run_fn or applescript.run
    raw = run_fn(_READ_TODAY)  # extend with tomorrow/week scripts as needed
    return parse_events(raw)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_calendar_tool.py -v`
Expected: PASS.

- [ ] **Step 5: Live check (manual, triggers permission prompt)**

Run: `python -c "from app.tools import calendar_tool as c; print(c.get_events())"`
Expected: first run shows a macOS Automation permission prompt → allow → prints today's events (or `[]`).

- [ ] **Step 6: Commit**

```bash
git add app/tools/calendar_tool.py tests/test_calendar_tool.py && git commit -m "feat: read Apple Calendar events with tests"
```

### Task 11: `app/tools/mail_tool.py` (read mail)

**Files:**
- Create: `app/tools/mail_tool.py`
- Test: `tests/test_mail_tool.py`

**Interfaces:**
- Consumes: `applescript.run`.
- Produces: `parse_mails(raw: str) -> list[dict]` (`{"subject","sender"}`), `get_recent(unread_only=True, limit=10, run_fn=applescript.run) -> list[dict]`. `send_mail(...)` added in Task 14.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_mail_tool.py
from app.tools import mail_tool

def test_parse_mails():
    raw = "Fatura|bank@x.com\nMerhaba|ali@y.com"
    assert mail_tool.parse_mails(raw) == [
        {"subject": "Fatura", "sender": "bank@x.com"},
        {"subject": "Merhaba", "sender": "ali@y.com"},
    ]

def test_get_recent_uses_run_fn():
    out = mail_tool.get_recent(run_fn=lambda s: "Konu|a@b.com")
    assert out == [{"subject": "Konu", "sender": "a@b.com"}]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_mail_tool.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

```python
# app/tools/mail_tool.py
from app.tools import applescript

_READ_UNREAD = '''
set output to ""
tell application "Mail"
  set msgs to (messages of inbox whose read status is false)
  set n to 0
  repeat with m in msgs
    if n >= {limit} then exit repeat
    set output to output & (subject of m) & "|" & (sender of m) & linefeed
    set n to n + 1
  end repeat
end tell
return output
'''

def parse_mails(raw):
    mails = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or "|" not in line:
            continue
        subject, sender = line.split("|", 1)
        mails.append({"subject": subject.strip(), "sender": sender.strip()})
    return mails

def get_recent(unread_only=True, limit=10, run_fn=None):
    run_fn = run_fn or applescript.run
    raw = run_fn(_READ_UNREAD.replace("{limit}", str(limit)))
    return parse_mails(raw)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_mail_tool.py -v`
Expected: PASS.

- [ ] **Step 5: Live check (manual, triggers permission prompt)**

Run: `python -c "from app.tools import mail_tool as m; print(m.get_recent())"`
Expected: Automation prompt → allow → prints unread subjects/senders (or `[]`).

- [ ] **Step 6: Commit**

```bash
git add app/tools/mail_tool.py tests/test_mail_tool.py && git commit -m "feat: read Apple Mail unread messages with tests"
```

---

## Phase 7 — Orchestrator (read) + confirmed write actions

### Task 12: `app/assistant.py` (read flows)

**Files:**
- Create: `app/assistant.py`
- Test: `tests/test_assistant.py`

**Interfaces:**
- Consumes: `router.route`, `retriever.get_top_chunks`, `calendar_tool.get_events`, `mail_tool.get_recent`, `llm.chat`.
- Produces:
  - `SYSTEM_PROMPT: str`
  - `answer(query: str, deps: dict | None = None) -> dict` with keys `text: str`, `sources: list[str]`, `pending_action: dict | None`. `deps` injects `route/retrieve/calendar/mail/chat` callables for testing. For read queries `pending_action` is `None`. For write queries it builds a draft (Task 13/14) and returns it WITHOUT executing.

- [ ] **Step 1: Write the failing test (all deps injected)**

```python
# tests/test_assistant.py
from app import assistant

def deps(**over):
    base = {
        "route": lambda q: {"tool": "documents", "action": "read"},
        "retrieve": lambda q: [("faq.md", "Kireç için X yapın.", 0.9)],
        "calendar": lambda: [{"title": "Dişçi", "start": "2026-07-04 15:00"}],
        "mail": lambda: [{"subject": "Fatura", "sender": "b@x.com"}],
        "chat": lambda system, user: "MODEL_CEVABI",
    }
    base.update(over)
    return base

def test_document_answer_includes_sources():
    res = assistant.answer("Kireç nasıl temizlenir?", deps=deps())
    assert res["text"] == "MODEL_CEVABI"
    assert res["sources"] == ["faq.md"]
    assert res["pending_action"] is None

def test_document_no_context_says_unknown():
    res = assistant.answer("Alakasız soru", deps=deps(retrieve=lambda q: []))
    assert "bilgi" in res["text"].lower()
    assert res["pending_action"] is None

def test_calendar_read_summarizes():
    res = assistant.answer("Bugün ne var?",
                           deps=deps(route=lambda q: {"tool": "calendar", "action": "read"}))
    assert res["text"] == "MODEL_CEVABI"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_assistant.py -v`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation (read flows; write raises NotImplemented placeholder to be filled in Task 13/14)**

```python
# app/assistant.py
from app import router, retriever, llm
from app.tools import calendar_tool, mail_tool

SYSTEM_PROMPT = (
    "Sen yardımcı bir Türkçe asistansın. SADECE sana verilen BAĞLAM'ı kullanarak yanıt ver. "
    "Bağlamda cevap yoksa 'Bu konuda bilgim yok.' de. Mümkünse kaynağı belirt. Kısa ve net ol."
)
NO_INFO = "Belgelerimde bu konuda bilgi yok."

def _default_deps():
    return {
        "route": router.route,
        "retrieve": retriever.get_top_chunks,
        "calendar": calendar_tool.get_events,
        "mail": mail_tool.get_recent,
        "chat": llm.chat,
    }

def answer(query, deps=None):
    d = deps or _default_deps()
    decision = d["route"](query)
    tool, action = decision["tool"], decision["action"]

    if action == "write":
        return _draft_write(query, tool, d)  # defined in Task 13/14

    if tool == "documents":
        chunks = d["retrieve"](query)
        if not chunks:
            return {"text": NO_INFO, "sources": [], "pending_action": None}
        context = "\n\n".join(f"[{s}] {t}" for (s, t, _score) in chunks)
        text = d["chat"](SYSTEM_PROMPT, f"BAĞLAM:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": [s for (s, _t, _sc) in chunks], "pending_action": None}

    if tool == "calendar":
        events = d["calendar"]()
        context = "\n".join(f"- {e['title']} ({e['start']})" for e in events) or "(etkinlik yok)"
        text = d["chat"](SYSTEM_PROMPT, f"BUGÜNKÜ ETKİNLİKLER:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": ["Apple Takvim"], "pending_action": None}

    if tool == "mail":
        mails = d["mail"]()
        context = "\n".join(f"- {m['subject']} — {m['sender']}" for m in mails) or "(mail yok)"
        text = d["chat"](SYSTEM_PROMPT, f"OKUNMAMIŞ MAİLLER:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": ["Apple Mail"], "pending_action": None}

    text = d["chat"](SYSTEM_PROMPT, query)
    return {"text": text, "sources": [], "pending_action": None}

def _draft_write(query, tool, d):
    raise NotImplementedError  # implemented in Task 13 (calendar) / Task 14 (mail)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_assistant.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/assistant.py tests/test_assistant.py && git commit -m "feat: assistant orchestrator (read flows) with tests"
```

### Task 13: Confirmed calendar write (`create_event` + draft + confirm)

**Files:**
- Modify: `app/tools/calendar_tool.py`
- Modify: `app/assistant.py`
- Test: `tests/test_calendar_tool.py`, `tests/test_assistant.py`

**Interfaces:**
- Produces: `calendar_tool.create_event(title, start, end, run_fn=applescript.run) -> bool`; `assistant._draft_write` for calendar returns `pending_action = {"type":"calendar","title","start","end"}`; `assistant.confirm(pending_action, deps=None) -> str`.

- [ ] **Step 1: Write failing tests**

```python
# add to tests/test_calendar_tool.py
def test_create_event_builds_and_runs():
    captured = {}
    def run_fn(script): captured["s"] = script; return ""
    ok = calendar_tool.create_event("Dişçi", "2026-07-04 15:00", "2026-07-04 16:00", run_fn=run_fn)
    assert ok is True
    assert "Dişçi" in captured["s"]

# add to tests/test_assistant.py
def test_calendar_write_returns_pending_not_executed():
    res = assistant.answer("Yarın 15:00 dişçi randevusu ekle",
                           deps=deps(route=lambda q: {"tool": "calendar", "action": "write"}))
    assert res["pending_action"]["type"] == "calendar"
    assert res["text"]  # a human-readable confirmation prompt

def test_confirm_calendar_calls_create():
    called = {}
    d = deps()
    d["create_event"] = lambda **kw: called.setdefault("kw", kw) or True
    pa = {"type": "calendar", "title": "Dişçi", "start": "2026-07-04 15:00", "end": "2026-07-04 16:00"}
    msg = assistant.confirm(pa, deps=d)
    assert called["kw"]["title"] == "Dişçi"
    assert "eklendi" in msg.lower()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_calendar_tool.py tests/test_assistant.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `app/tools/calendar_tool.py`:
```python
_CREATE = '''
set startDate to date "{start}"
set endDate to date "{end}"
tell application "Calendar"
  tell calendar 1
    make new event with properties {{summary:"{title}", start date:startDate, end date:endDate}}
  end tell
end tell
return "ok"
'''

def create_event(title, start, end, run_fn=None):
    run_fn = run_fn or applescript.run
    script = _CREATE.format(title=title.replace('"', "'"), start=start, end=end)
    run_fn(script)
    return True
```

Update `app/assistant.py` — replace `_draft_write` and add `confirm`, plus a naive draft parser. Add near top: `from app.tools import calendar_tool, mail_tool` (already imported). Implement:
```python
import re
from datetime import datetime, timedelta

def _parse_calendar_draft(query):
    # Extract HH:MM and a title; default duration 1h; date today/tomorrow by keyword.
    m = re.search(r"(\d{1,2})[:.](\d{2})", query)
    hour, minute = (int(m.group(1)), int(m.group(2))) if m else (9, 0)
    base = datetime.now()
    if "yarın" in query.lower():
        base = base + timedelta(days=1)
    start = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
    end = start + timedelta(hours=1)
    title = re.sub(r"\d{1,2}[:.]\d{2}", "", query)
    for w in ("yarın", "bugün", "ekle", "oluştur", "randevu", "randevusu", "kur"):
        title = title.replace(w, "").replace(w.capitalize(), "")
    title = title.strip(" ,.-") or "Etkinlik"
    fmt = "%Y-%m-%d %H:%M"
    return {"type": "calendar", "title": title,
            "start": start.strftime(fmt), "end": end.strftime(fmt)}

def _draft_write(query, tool, d):
    if tool == "calendar":
        pa = _parse_calendar_draft(query)
        text = (f"Şu etkinliği eklememi ister misin?\n"
                f"  Başlık: {pa['title']}\n  Başlangıç: {pa['start']}\n  Bitiş: {pa['end']}\n"
                f"(Onaylıyor musun?)")
        return {"text": text, "sources": [], "pending_action": pa}
    if tool == "mail":
        return _draft_mail(query, d)  # Task 14
    return {"text": "Bu işlemi yapamıyorum.", "sources": [], "pending_action": None}

def confirm(pending_action, deps=None):
    d = deps or _default_deps()
    if pending_action["type"] == "calendar":
        create = d.get("create_event", calendar_tool.create_event)
        create(title=pending_action["title"], start=pending_action["start"], end=pending_action["end"])
        return "Etkinlik takvime eklendi. ✓"
    if pending_action["type"] == "mail":
        send = d.get("send_mail", mail_tool.send_mail)
        send(to=pending_action["to"], subject=pending_action["subject"], body=pending_action["body"])
        return "E-posta gönderildi. ✓"
    return "Bilinmeyen işlem."
```
Also add `"create_event"` and `"send_mail"` to `_default_deps()` return dict:
```python
        "create_event": calendar_tool.create_event,
        "send_mail": mail_tool.send_mail,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_calendar_tool.py tests/test_assistant.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/tools/calendar_tool.py app/assistant.py tests/ && git commit -m "feat: confirmed calendar event creation (draft→confirm)"
```

### Task 14: Confirmed mail send (`send_mail` + draft)

**Files:**
- Modify: `app/tools/mail_tool.py`, `app/assistant.py`
- Test: `tests/test_mail_tool.py`, `tests/test_assistant.py`

**Interfaces:**
- Produces: `mail_tool.send_mail(to, subject, body, run_fn=applescript.run) -> bool`; `assistant._draft_mail(query, d)` returns `pending_action = {"type":"mail","to","subject","body"}`.

- [ ] **Step 1: Write failing tests**

```python
# add to tests/test_mail_tool.py
def test_send_mail_builds_script():
    cap = {}
    ok = mail_tool.send_mail("a@b.com", "Konu", "Gövde", run_fn=lambda s: cap.setdefault("s", s) or "")
    assert ok is True
    assert "a@b.com" in cap["s"] and "Konu" in cap["s"]

# add to tests/test_assistant.py
def test_mail_write_returns_pending():
    res = assistant.answer("a@b.com adresine 'Konu' başlıklı mail gönder: Merhaba",
                           deps=deps(route=lambda q: {"tool": "mail", "action": "write"}))
    pa = res["pending_action"]
    assert pa["type"] == "mail" and pa["to"] == "a@b.com"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_mail_tool.py tests/test_assistant.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement**

Add to `app/tools/mail_tool.py`:
```python
_SEND = '''
tell application "Mail"
  set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:true}}
  tell newMessage
    make new to recipient at end of to recipients with properties {{address:"{to}"}}
  end tell
  send newMessage
end tell
return "ok"
'''

def send_mail(to, subject, body, run_fn=None):
    run_fn = run_fn or applescript.run
    script = _SEND.format(
        to=to, subject=subject.replace('"', "'"), body=body.replace('"', "'"),
    )
    run_fn(script)
    return True
```

Add to `app/assistant.py`:
```python
def _draft_mail(query, d):
    to = None
    m = re.search(r"[\w.\-]+@[\w.\-]+", query)
    if m:
        to = m.group(0)
    subj = re.search(r"'([^']+)'", query)
    subject = subj.group(1) if subj else "(konu yok)"
    body = query.split(":", 1)[1].strip() if ":" in query else "(içerik yok)"
    if not to:
        return {"text": "Kime göndereceğimi anlayamadım. E-posta adresi verir misin?",
                "sources": [], "pending_action": None}
    pa = {"type": "mail", "to": to, "subject": subject, "body": body}
    text = (f"Şu e-postayı göndermemi ister misin?\n"
            f"  Kime: {to}\n  Konu: {subject}\n  İçerik: {body}\n(Onaylıyor musun?)")
    return {"text": text, "sources": [], "pending_action": pa}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_mail_tool.py tests/test_assistant.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/tools/mail_tool.py app/assistant.py tests/ && git commit -m "feat: confirmed mail send (draft→confirm)"
```

---

## Phase 8 — User interfaces

### Task 15: `ui/cli.py`

**Files:**
- Create: `ui/cli.py`

**Interfaces:**
- Consumes: `assistant.answer`, `assistant.confirm`.
- Produces: a `main()` REPL loop. Read queries print text + sources. `pending_action` prompts `Onayla (e/h)`; on `e` calls `assistant.confirm`.

- [ ] **Step 1: Implement**

```python
# ui/cli.py
from app import assistant

def main():
    print("personas — Kişisel Asistan (çıkış: 'q')")
    while True:
        try:
            query = input("\nSen> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
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
```

- [ ] **Step 2: Manual smoke test**

Run: `python -m ui.cli` → ask a document question, a calendar question, and "yarın 15:00 test etkinliği ekle" then answer `h` (do not create).
Expected: sensible answers; the write path asks for confirmation and cancels on `h`.

- [ ] **Step 3: Commit**

```bash
git add ui/cli.py && git commit -m "feat: CLI interface with confirmation"
```

### Task 16: `ui/web.py` (Streamlit)

**Files:**
- Create: `ui/web.py`

**Interfaces:**
- Consumes: `assistant.answer`, `assistant.confirm`. Uses `st.session_state` for chat history and a pending action.

- [ ] **Step 1: Implement**

```python
# ui/web.py
import streamlit as st
from app import assistant

st.set_page_config(page_title="personas", page_icon="🤖")
st.title("🤖 personas — Kişisel Asistan")

if "history" not in st.session_state:
    st.session_state.history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.write(text)

if st.session_state.pending:
    st.warning("Bu işlemi onaylıyor musun?")
    col1, col2 = st.columns(2)
    if col1.button("✅ Onayla"):
        msg = assistant.confirm(st.session_state.pending)
        st.session_state.history.append(("assistant", msg))
        st.session_state.pending = None
        st.rerun()
    if col2.button("❌ İptal"):
        st.session_state.history.append(("assistant", "İptal edildi."))
        st.session_state.pending = None
        st.rerun()

query = st.chat_input("Bir şey sor...")
if query:
    st.session_state.history.append(("user", query))
    res = assistant.answer(query)
    text = res["text"]
    if res["sources"]:
        text += f"\n\n_(Kaynak: {', '.join(res['sources'])})_"
    st.session_state.history.append(("assistant", text))
    st.session_state.pending = res["pending_action"]
    st.rerun()
```

- [ ] **Step 2: Manual smoke test**

Run: `streamlit run ui/web.py`
Expected: browser chat UI; document/calendar/mail questions answer; write intents show Onayla/İptal buttons.

- [ ] **Step 3: Commit**

```bash
git add ui/web.py && git commit -m "feat: Streamlit web interface with confirmation buttons"
```

---

## Phase 9 — Setup check, seed data, docs

### Task 17: `scripts/setup_check.py`

**Files:**
- Create: `scripts/setup_check.py`

**Interfaces:**
- Produces: a script that prints PASS/FAIL for: `foundry` on PATH, chat model loads, `llm.embed` returns a vector, DB writable.

- [ ] **Step 1: Implement**

```python
# scripts/setup_check.py
import shutil, sys
from app import config, llm, store

def check(name, fn):
    try:
        fn(); print(f"[PASS] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {e}")

def main():
    check("foundry PATH'te", lambda: (_ for _ in ()).throw(RuntimeError("foundry bulunamadı"))
          if shutil.which("foundry") is None else None)
    check("chat modeli", lambda: llm.chat("Kısa cevap.", "merhaba"))
    check("embedding", lambda: llm.embed(["deneme"]))
    check("veritabanı yazılabilir", lambda: (store.init_db(), store.count()))

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it**

Run: `python -m scripts.setup_check`
Expected: four PASS lines (with Foundry running and models present).

- [ ] **Step 3: Commit**

```bash
git add scripts/setup_check.py && git commit -m "feat: environment setup check script"
```

### Task 18: Seed documents + README + final push

**Files:**
- Create: `data/documents/macos-kisayollar.md`, `data/documents/terminal-komutlar.md`, `data/documents/git-notlari.md`
- Create: `README.md`

- [ ] **Step 1: Add 3 short seed documents**

`data/documents/macos-kisayollar.md` (example):
```markdown
# macOS Kısayolları

Ekran görüntüsü (bölge): Cmd + Shift + 4, sonra imleçle bölgeyi seç.
Ekran görüntüsü (tüm ekran): Cmd + Shift + 3.
Spotlight arama: Cmd + Boşluk.
Uygulamalar arası geçiş: Cmd + Tab.
```
Add similar short files for terminal commands and git notes (each a few `\n\n`-separated lines so chunking produces multiple chunks).

- [ ] **Step 2: Write `README.md`**

Include: proje amacı, kurulum (Homebrew → Foundry Local → venv → `pip install`), `foundry model list` ile alias doğrulama, `python -m app.ingest`, `python -m ui.cli`, `streamlit run ui/web.py`, izinler (Automation), sınırlar (offline, küçük model, sadece onaylı yazma). Reference the spec at `docs/specs/2026-07-03-kisisel-asistan-design.md`.

- [ ] **Step 3: Ingest seed docs and run full test suite**

Run:
```bash
python -m app.ingest
pytest -v
```
Expected: ingest prints a chunk count > 3; all tests PASS.

- [ ] **Step 4: Commit and push**

```bash
git add data/documents README.md && git commit -m "docs: seed documents and README"
git push
```

---

## Self-Review Notes (author checklist — completed)

- **Spec coverage:** RAG (Tasks 2–7,12), calendar read (10) + write (13), mail read (11) + write (14), router incl. write intent (8), confirmation flow (13,14, UIs 15–16), error handling (9 AppleScript, 12 no-info, threshold in 7), tests (each task), setup/GitHub (0.1–0.3, 17), offline/small-model constraints (Global Constraints), CLI+Streamlit (15,16), private repo `personas` (0.3). ✅
- **Placeholder scan:** `_draft_write` intentionally raises `NotImplementedError` in Task 12 and is fully implemented in Task 13 — noted explicitly, not a stray placeholder. No TBDs. ✅
- **Type consistency:** `answer()` always returns `{text, sources, pending_action}`; `pending_action` shapes `{"type":"calendar",title,start,end}` / `{"type":"mail",to,subject,body}` consistent across assistant, confirm, and UIs. `route()` returns `{tool,action}` consistently. `create_event(title,start,end)` / `send_mail(to,subject,body)` signatures match calls in `confirm`. ✅
- **Known risk:** Foundry Local SDK method names and model aliases must be confirmed against the installed version (Tasks 0.1, 5); embedding fallback documented.
