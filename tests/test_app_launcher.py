"""Uygulama açma: kısaltmalar, Türkçe ekler ve kurulu uygulamalarla eşleşme."""
import pytest

from app.tools import app_launcher

KURULU = ["WhatsApp", "Google Chrome", "Spotify", "Discord", "Visual Studio Code",
          "Calculator", "Notes", "Safari", "Telegram", "Zoom"]


def coz(ad):
    return app_launcher.resolve_app_name(ad, apps=KURULU)


@pytest.mark.parametrize("girdi,beklenen", [
    ("not defteri", "Notes"),
    ("Hesap Makinesi", "Calculator"),
    ("spotify", "Spotify"),
])
def test_turkish_aliases(girdi, beklenen):
    assert coz(girdi) == beklenen


@pytest.mark.parametrize("girdi", ["wp", "WP", "wpp", "vatsap"])
def test_whatsapp_abbreviations(girdi):
    assert coz(girdi) == "WhatsApp"


@pytest.mark.parametrize("girdi,beklenen", [
    ("whatsappı", "WhatsApp"),
    ("whatsapp'ı", "WhatsApp"),
    ("spotify'ı", "Spotify"),
    ("chrome'u", "Google Chrome"),
    ("discord'u", "Discord"),
    ("telegramı", "Telegram"),
])
def test_turkish_suffixes_are_stripped(girdi, beklenen):
    assert coz(girdi) == beklenen


def test_word_ending_in_a_vowel_is_not_mangled():
    # "safari" sonundaki 'i' ek değil; "safar"a indirgenmemeli.
    assert coz("safari") == "Safari"


@pytest.mark.parametrize("girdi,beklenen", [
    ("diskord", "Discord"),
    ("whatsap", "WhatsApp"),
    ("zoomu", "Zoom"),
])
def test_typos_match_installed_apps(girdi, beklenen):
    assert coz(girdi) == beklenen


def test_unknown_app_is_reported_clearly():
    with pytest.raises(app_launcher.AppLaunchError) as hata:
        app_launcher.open_app("kesinlikle olmayan uygulama", apps=KURULU,
                              run_fn=lambda a: (_ for _ in ()).throw(
                                  app_launcher.AppLaunchError("yok")))
    assert "kesinlikle olmayan uygulama" in str(hata.value) or "yok" in str(hata.value)


def test_open_app_uses_run_fn_and_returns_resolved():
    cap = {}
    opened = app_launcher.open_app("wp", apps=KURULU, run_fn=lambda a: cap.setdefault("a", a))
    assert opened == "WhatsApp" and cap["a"] == "WhatsApp"


def test_installed_apps_reads_the_system():
    adlar = app_launcher.installed_apps()
    assert isinstance(adlar, list)
    # Bu makinede en az bir uygulama olmalı; içerik makineye göre değişir.
    assert adlar


def test_missing_app_suggests_the_closest_installed_one():
    def patla(app):
        raise app_launcher.AppLaunchError(f"{app} yok")

    with pytest.raises(app_launcher.AppLaunchError) as hata:
        app_launcher.open_app("zoome", apps=["Zoom", "Notes"], run_fn=patla)
    assert "Zoom" in str(hata.value)
