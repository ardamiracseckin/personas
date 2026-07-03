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
            "'foundry model load phi-3.5-mini' (servis otomatik başlar)."
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


def _client():
    """Lazy-init the OpenAI client against Foundry Local. Returns (client, model_id)."""
    global _openai, _model_id
    if _openai is None:
        from openai import OpenAI

        _openai = OpenAI(base_url=_discover_base_url(), api_key="not-needed")
    if _model_id is None:
        ids = [m.id for m in _openai.models.list().data]
        if not ids:
            _ensure_model_loaded()
            ids = [m.id for m in _openai.models.list().data]
        want = config.CHAT_MODEL.lower()
        _model_id = next((i for i in ids if i.lower().startswith(want)), ids[0] if ids else None)
        if _model_id is None:
            raise RuntimeError(
                "Foundry Local'de yüklü model bulunamadı. "
                "'foundry model load phi-3.5-mini' çalıştırın."
            )
    return _openai, _model_id


def chat(system, user):
    client, model_id = _client()
    resp = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def _embedder():
    global _embedder_obj
    if _embedder_obj is None:
        from fastembed import TextEmbedding

        _embedder_obj = TextEmbedding(model_name=config.EMBED_MODEL)
    return _embedder_obj


def embed(texts):
    model = _embedder()
    return [vec.tolist() for vec in model.embed(list(texts))]
