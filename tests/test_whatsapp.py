"""WhatsApp: numara normalleştirme ve taslak/otomatik gönderim."""
import pytest

import app.config as config
from app.tools import whatsapp


@pytest.mark.parametrize("ham,beklenen", [
    ("0555 111 22 33", "905551112233"),
    ("+90 555 111 22 33", "905551112233"),
    ("905551112233", "905551112233"),
    ("555 111 22 33", "905551112233"),
    ("(0532) 444-5566", "905324445566"),
])
def test_phone_normalisation(ham, beklenen):
    assert whatsapp.normalize_phone(ham) == beklenen


def test_foreign_number_is_kept():
    assert whatsapp.normalize_phone("+1 415 555 0100") == "14155550100"


def test_invalid_phone_is_rejected():
    with pytest.raises(ValueError):
        whatsapp.normalize_phone("123")


def test_draft_url_encodes_the_message():
    url = whatsapp.draft_url("905551112233", "Yarın 14:00 uygun mu?")
    assert url.startswith("whatsapp://send?phone=905551112233&text=")
    assert "Yar%C4%B1n" in url and "%3F" in url


def test_open_draft_calls_open_with_the_url():
    yakalanan = {}
    whatsapp.send("0555 111 22 33", "selam", auto=False,
                  open_fn=lambda url: yakalanan.setdefault("url", url))
    assert yakalanan["url"].startswith("whatsapp://send?phone=905551112233")


def test_auto_send_presses_return_after_opening():
    adimlar = []
    whatsapp.send("0555 111 22 33", "selam", auto=True,
                  open_fn=lambda url: adimlar.append("ac"),
                  keystroke_fn=lambda: adimlar.append("enter"))
    assert adimlar == ["ac", "enter"]


def test_default_mode_follows_config(monkeypatch):
    monkeypatch.setattr(config, "WHATSAPP_AUTO_SEND", True)
    adimlar = []
    whatsapp.send("0555 111 22 33", "selam",
                  open_fn=lambda url: adimlar.append("ac"),
                  keystroke_fn=lambda: adimlar.append("enter"))
    assert adimlar == ["ac", "enter"]
