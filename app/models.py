"""Foundry Local model yönetimi: hangi model indirilmiş, hangisi yüklü, nasıl değişir.

8 GB bellekte aynı anda tek model tutulabildiği için değişim "eskisini boşalt,
yenisini yükle" biçimindedir ve saniyeler sürer. Arayüz bu süreyi kullanıcıya
gösterebilsin diye işlem tek bir çağrıda toplandı.
"""
import json
import subprocess

from app import config, llm

LOAD_TIMEOUT = 600
LIST_TIMEOUT = 60


def _foundry():
    return llm._foundry_exe()


def _run(*args, timeout=LIST_TIMEOUT):
    return subprocess.run([_foundry(), *args], capture_output=True, text=True, timeout=timeout)


def cache_entries():
    """Önbellekteki modeller: [{alias, cached, loaded}].

    0.10 ile `foundry cache ls -o json` geldi; eski sürümlerde metin tablosu
    ayrıştırılır (orada yüklü bilgisi yoktur).
    """
    try:
        ham = _run("cache", "ls", "-o", "json").stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []
    try:
        return json.loads(ham).get("models", [])
    except (json.JSONDecodeError, AttributeError):
        pass

    kayitlar = []
    for satir in ham.splitlines():
        parcalar = satir.replace("💾", " ").split()
        if len(parcalar) >= 2 and not satir.strip().startswith(("Models", "Alias", "[", "+", "|")):
            kayitlar.append({"alias": parcalar[0], "cached": True, "loaded": False})
    return kayitlar


def downloaded_aliases():
    """İndirilmiş model takma adları."""
    return {k["alias"] for k in cache_entries() if k.get("cached", True)}


def catalog():
    """Arayüz için model listesi: indirilmiş mi, şu an aktif mi."""
    indirilen = downloaded_aliases()
    return [
        {**model,
         "indirildi": model["alias"] in indirilen,
         "aktif": model["alias"] == config.CHAT_MODEL}
        for model in config.MODEL_CATALOG
    ]


def current():
    return config.CHAT_MODEL


def _load(alias):
    return _run("model", "load", alias, timeout=LOAD_TIMEOUT)


def is_loaded(alias=None):
    """Yapılandırılan model şu an bellekte mi?"""
    alias = (alias or config.CHAT_MODEL).lower()
    return any(k.get("alias", "").lower() == alias and k.get("loaded")
               for k in cache_entries())


def ensure_loaded(alias=None):
    """Model bellekte değilse yükle. Sunucu açılışında arka planda çağrılır."""
    alias = alias or config.CHAT_MODEL
    if is_loaded(alias):
        return True
    try:
        return _load(alias).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def supports_images(alias=None):
    alias = alias or config.CHAT_MODEL
    return any(m["alias"] == alias and m["gorsel"] for m in config.MODEL_CATALOG)


def switch(alias):
    """Aktif modeli değiştir. Eski model bellekten boşaltılır, yenisi yüklenir."""
    bilinen = [m["alias"] for m in config.MODEL_CATALOG]
    if alias not in bilinen:
        raise ValueError(f"Bilinmeyen model: {alias}. Seçenekler: {', '.join(bilinen)}")

    onceki = config.CHAT_MODEL
    if onceki and onceki != alias:
        _run("model", "unload", onceki, timeout=LOAD_TIMEOUT)
    sonuc = _load(alias)
    if sonuc.returncode != 0:
        # Yükleme başarısızsa bellekte hiç model kalmaz ve asistan tamamen durur;
        # eski modeli geri yükleyip hatayı öyle bildiriyoruz.
        if onceki and onceki != alias:
            _load(onceki)
        raise RuntimeError(f"'{alias}' yüklenemedi: {(sonuc.stderr or sonuc.stdout).strip()[:200]}")

    config.CHAT_MODEL = alias
    llm.reset()  # önbellekteki model kimliği artık geçersiz
    return alias
