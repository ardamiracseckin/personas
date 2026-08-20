"""LLM access: chat via Foundry Local, embeddings via fastembed (local, offline).

Foundry Local exposes an OpenAI-compatible HTTP API on a dynamic local port. We
discover that endpoint (env override or `foundry service status`) instead of
hardcoding it, then talk to it with the standard `openai` client. Embeddings use
a small multilingual model through fastembed, since Foundry Local's catalog has
no embedding model. Everything is lazily initialised and runs offline once the
models are present.
"""
import os
import re
import shutil
import subprocess

from app import config

_openai = None
_model_id = None
_embedder_obj = None


def _foundry_exe():
    return shutil.which("foundry") or "/opt/homebrew/bin/foundry"


def _discover_base_url():
    """Return the Foundry Local OpenAI base URL (…/v1)."""
    override = os.environ.get("FOUNDRY_BASE_URL")
    if override:
        return override.rstrip("/")
    try:
        out = subprocess.run(
            [_foundry_exe(), "service", "status"],
            capture_output=True, text=True, timeout=20,
        ).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        out = ""
    m = re.search(r"http://127\.0\.0\.1:\d+", out)
    if not m:
        raise RuntimeError(
            "Foundry Local servisine ulaşılamadı. Terminalde şunu çalıştırın: "
            f"'foundry model load {config.CHAT_MODEL}' (servis otomatik başlar)."
        )
    return m.group(0) + "/v1"


def _ensure_model_loaded():
    """Best-effort: load the chat model via CLI if it isn't already."""
    try:
        subprocess.run(
            [_foundry_exe(), "model", "load", config.CHAT_MODEL],
            capture_output=True, text=True, timeout=180,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def pick_model(ids, alias):
    """Takma adla başlayan model kimliğini seç; eşleşme yoksa None.

    Başka bir modele düşmek yok: yanlış modelle cevap üretmek, hata vermekten
    daha kötüdür (ölçümler ve demo sessizce başka modeli kullanabilirdi).
    """
    want = alias.lower()
    return next((i for i in ids if i.lower().startswith(want)), None)


def _client():
    """Lazy-init the OpenAI client against Foundry Local. Returns (client, model_id)."""
    global _openai, _model_id
    if _openai is None:
        from openai import OpenAI

        _openai = OpenAI(base_url=_discover_base_url(), api_key="not-needed")
    if _model_id is None:
        ids = [m.id for m in _openai.models.list().data]
        _model_id = pick_model(ids, config.CHAT_MODEL)
        if _model_id is None:
            _ensure_model_loaded()  # yapılandırılan model yüklü değil: yüklemeyi dene
            ids = [m.id for m in _openai.models.list().data]
            _model_id = pick_model(ids, config.CHAT_MODEL)
        if _model_id is None:
            yuklu = ", ".join(ids) if ids else "yok"
            raise RuntimeError(
                f"'{config.CHAT_MODEL}' Foundry Local'de yüklü değil (yüklü olanlar: {yuklu}). "
                f"Çalıştırın: foundry model load {config.CHAT_MODEL}"
            )
    return _openai, _model_id


def reset():
    """Önbelleklenmiş istemciyi ve model kimliğini unut (model değiştirince gerekir)."""
    global _openai, _model_id
    _openai, _model_id = None, None


def _messages(system, user, image_b64=None):
    """OpenAI biçiminde mesajlar. Görsel varsa içerik dizi hâline gelir."""
    if not image_b64:
        icerik = user
    else:
        icerik = [
            {"type": "text", "text": user},
            {"type": "image_url",
             "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": icerik},
    ]


def chat(system, user, image_b64=None):
    client, model_id = _client()
    resp = client.chat.completions.create(
        model=model_id,
        messages=_messages(system, user, image_b64),
        temperature=0.2,
        max_tokens=config.MAX_TOKENS,
    )
    return resp.choices[0].message.content.strip()


def chat_stream(system, user, image_b64=None):
    """chat() ile aynı istek; cevabı geldikçe parça parça verir.

    Küçük modelde tam cevap saniyeler sürüyor; arayüzün boş beklemesi yerine
    ilk kelimeleri hemen göstermek algılanan gecikmeyi belirgin biçimde düşürür.
    """
    client, model_id = _client()
    stream = client.chat.completions.create(
        model=model_id,
        messages=_messages(system, user, image_b64),
        temperature=0.2,
        max_tokens=config.MAX_TOKENS,
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def _embedder():
    global _embedder_obj
    if _embedder_obj is None:
        from fastembed import TextEmbedding

        _embedder_obj = TextEmbedding(model_name=config.EMBED_MODEL)
    return _embedder_obj


def embed(texts):
    model = _embedder()
    return [vec.tolist() for vec in model.embed(list(texts))]
