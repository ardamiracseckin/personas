"""Mevzuat soru setinin sağlamlığı.

Ölçüm setindeki bir hata bütün sonuçları sessizce bozar: olmayan bir maddeye
atıf, tekrarlanan kimlik, ya da bilgi tabanında bulunmayan bir kanun. Bu testler
seti veri olarak doğrular ve beklenen her maddenin korpusta gerçekten var
olduğunu kontrol eder.
"""
import json
import re
from pathlib import Path

import pytest

from app import config, store

KOK = Path(__file__).resolve().parent.parent
SORULAR = json.loads((KOK / "eval" / "mevzuat_sorular.json").read_text(encoding="utf-8"))["questions"]
KATEGORILER = {"cevaplanabilir", "cevaplanamaz", "tahmin", "uc_durum"}


def _mevzuat_yuklu():
    if not config.DB_PATH.exists() or store.count() == 0:
        return False
    return any("sayılı" in kaynak for (kaynak, _adet) in store.sources())


def test_ids_are_unique():
    kimlikler = [s["id"] for s in SORULAR]
    assert len(kimlikler) == len(set(kimlikler))


def test_every_category_is_represented():
    assert {s["category"] for s in SORULAR} == KATEGORILER


def test_answerable_questions_declare_law_article_and_area():
    for s in SORULAR:
        if s["category"] == "cevaplanabilir":
            assert s.get("kanun"), s["id"]
            assert s.get("madde"), s["id"]
            assert s.get("alan"), s["id"]


def test_only_answerable_questions_declare_a_target():
    for s in SORULAR:
        if s["category"] != "cevaplanabilir":
            assert "kanun" not in s and "madde" not in s, s["id"]


def test_questions_are_not_empty_except_the_edge_case():
    bos = [s for s in SORULAR if not s["question"].strip()]
    assert len(bos) == 1 and bos[0]["category"] == "uc_durum"


@pytest.mark.skipif(not _mevzuat_yuklu(), reason="mevzuat bilgi tabanı yüklü değil")
def test_every_expected_article_exists_in_the_knowledge_base():
    """Beklenen madde korpusta gerçekten var mı — ezberden yazılmadığının kanıtı."""
    kunye = {t.splitlines()[0] for (_s, t, _e) in store.all_chunks()}
    for s in SORULAR:
        if s["category"] != "cevaplanabilir":
            continue
        desen = re.compile(rf"^{s['kanun']} sayılı .* md\. {re.escape(s['madde'])}(?: |—|$)")
        assert any(desen.match(k) for k in kunye), f"{s['id']}: {s['kanun']} md.{s['madde']} yok"
