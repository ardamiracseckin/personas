"""Model yönetimi: katalog, indirilmişler ve model değişimi."""
import json
import subprocess

import pytest

import app.config as config
from app import llm, models

CACHE_CIKTISI = json.dumps({"models": [
    {"alias": "phi-4-mini", "cached": True, "loaded": True},
    {"alias": "qwen3-vl-2b-instruct", "cached": True, "loaded": False},
]})


def sahte_run(kayit, cache_cikti=CACHE_CIKTISI, returncode=0):
    def _run(cmd, capture_output=True, text=True, timeout=None):
        kayit.append(cmd[1:])
        cikti = cache_cikti if cmd[1:3] == ["cache", "ls"] else "ok"
        return subprocess.CompletedProcess(cmd, returncode, stdout=cikti, stderr="")
    return _run


def test_downloaded_aliases_parses_cache_json(monkeypatch):
    monkeypatch.setattr(subprocess, "run", sahte_run([]))
    assert models.downloaded_aliases() == {"phi-4-mini", "qwen3-vl-2b-instruct"}


def test_catalog_marks_downloaded_and_active(monkeypatch):
    monkeypatch.setattr(subprocess, "run", sahte_run([]))
    monkeypatch.setattr(config, "CHAT_MODEL", "phi-4-mini")
    katalog = {m["alias"]: m for m in models.catalog()}
    assert katalog["phi-4-mini"]["aktif"] is True
    assert katalog["phi-4-mini"]["indirildi"] is True
    assert katalog["qwen2.5-1.5b"]["indirildi"] is False
    assert katalog["qwen2.5-1.5b"]["aktif"] is False


def test_switch_unloads_previous_then_loads_new(monkeypatch):
    kayit = []
    monkeypatch.setattr(subprocess, "run", sahte_run(kayit))
    monkeypatch.setattr(config, "CHAT_MODEL", "phi-4-mini")
    sifirlandi = {}
    monkeypatch.setattr(llm, "reset", lambda: sifirlandi.setdefault("evet", True))

    models.switch("qwen2.5-1.5b")

    assert kayit == [["model", "unload", "phi-4-mini"], ["model", "load", "qwen2.5-1.5b"]]
    assert config.CHAT_MODEL == "qwen2.5-1.5b"
    assert sifirlandi["evet"]  # istemci önbelleği temizlenmeli


def test_switch_to_the_same_model_does_not_unload(monkeypatch):
    kayit = []
    monkeypatch.setattr(subprocess, "run", sahte_run(kayit))
    monkeypatch.setattr(config, "CHAT_MODEL", "phi-4-mini")
    monkeypatch.setattr(llm, "reset", lambda: None)
    models.switch("phi-4-mini")
    assert kayit == [["model", "load", "phi-4-mini"]]


def test_unknown_model_is_rejected(monkeypatch):
    monkeypatch.setattr(llm, "reset", lambda: None)
    with pytest.raises(ValueError):
        models.switch("gpt-4")


def test_failed_load_raises(monkeypatch):
    monkeypatch.setattr(subprocess, "run", sahte_run([], returncode=1))
    monkeypatch.setattr(config, "CHAT_MODEL", "phi-4-mini")
    monkeypatch.setattr(llm, "reset", lambda: None)
    with pytest.raises(RuntimeError):
        models.switch("qwen2.5-1.5b")


def test_vision_flag_is_off_until_the_runtime_forwards_images():
    """Foundry uç noktası görseli modele iletmiyor; katalogda hiçbir model görsel değil."""
    assert models.supports_images("qwen3-vl-2b-instruct") is False
    assert models.supports_images("phi-4-mini") is False


def test_failed_load_restores_the_previous_model(monkeypatch):
    """Yükleme patlarsa ortada modelsiz kalınmamalı: eskisi geri yüklenir."""
    kayit = []

    def _run(cmd, capture_output=True, text=True, timeout=None):
        kayit.append(cmd[1:])
        # Yalnızca yeni modelin yüklenmesi başarısız olsun.
        basarisiz = cmd[1:3] == ["model", "load"] and cmd[3] == "qwen3-vl-2b-instruct"
        return subprocess.CompletedProcess(cmd, 1 if basarisiz else 0, stdout="hata", stderr="")

    monkeypatch.setattr(subprocess, "run", _run)
    monkeypatch.setattr(config, "CHAT_MODEL", "phi-4-mini")
    monkeypatch.setattr(llm, "reset", lambda: None)

    with pytest.raises(RuntimeError):
        models.switch("qwen3-vl-2b-instruct")

    assert kayit[-1][:3] == ["model", "load", "phi-4-mini"]  # eski model geri yüklendi
    assert config.CHAT_MODEL == "phi-4-mini"             # ayar da geri alındı




def test_ensure_loaded_skips_when_already_loaded(monkeypatch):
    kayit = []
    monkeypatch.setattr(models, "is_loaded", lambda alias=None: True)
    monkeypatch.setattr(subprocess, "run", sahte_run(kayit))
    assert models.ensure_loaded("phi-4-mini") is True
    assert kayit == []


def test_ensure_loaded_loads_when_missing(monkeypatch):
    kayit = []
    monkeypatch.setattr(models, "is_loaded", lambda alias=None: False)
    monkeypatch.setattr(subprocess, "run", sahte_run(kayit))
    assert models.ensure_loaded("phi-4-mini") is True
    assert kayit == [["model", "load", "phi-4-mini"]]
