"""macOS uygulamalarını (Türkçe) adıyla açar.

Ad çözümleme üç katmanlı: önce takma adlar ve kısaltmalar ("wp" → WhatsApp),
sonra kurulu uygulamalarla birebir/önek eşleşmesi, en sonda bulanık eşleşme
("diskord" → Discord). Türkçe ekler ("whatsappı", "chrome'u") ayrı bir aday
olarak denenir; doğrudan kesilmez, yoksa "safari" → "safar" olurdu.
"""
import re
import subprocess
from difflib import SequenceMatcher
from pathlib import Path

from app import lexical

APP_DIRS = (
    Path("/Applications"),
    Path("/Applications/Utilities"),
    Path("/System/Applications"),
    Path("/System/Applications/Utilities"),
    Path.home() / "Applications",
)

FUZZY_THRESHOLD = 0.75

# Anahtarlar sadeleştirilmiş hâlde (lexical.normalize): küçük harf, ASCII.
APP_ALIASES = {
    "not defteri": "Notes", "notlar": "Notes",
    "hesap makinesi": "Calculator", "hesap makinasi": "Calculator",
    "ayarlar": "System Settings", "sistem ayarlari": "System Settings",
    "safari": "Safari",
    "chrome": "Google Chrome", "google chrome": "Google Chrome",
    "spotify": "Spotify", "muzik": "Music",
    "takvim": "Calendar", "mail": "Mail", "posta": "Mail",
    "mesajlar": "Messages", "terminal": "Terminal",
    "fotograflar": "Photos",
    "kod": "Visual Studio Code", "vscode": "Visual Studio Code",
    "vs code": "Visual Studio Code", "vsc": "Visual Studio Code",
    "whatsapp": "WhatsApp", "telegram": "Telegram", "discord": "Discord",
    "haritalar": "Maps", "hava durumu": "Weather", "saat": "Clock",
    "onizleme": "Preview", "hesaplama": "Calculator",
    # Yaygın kısaltmalar ve konuşma dilindeki yazımlar
    "wp": "WhatsApp", "wpp": "WhatsApp", "wsp": "WhatsApp", "vatsap": "WhatsApp",
    "tg": "Telegram", "ig": "Instagram", "insta": "Instagram",
    "yt": "YouTube", "fb": "Facebook",
}

# Ada yapışmış Türkçe belirtme/yönelme ekleri: "whatsappı", "chrome'u", "telegrama"
_SUFFIX_RE = re.compile(r"(?:yi|yı|yu|yü|ni|nı|nu|nü|i|ı|u|ü|a|e)$")


class AppLaunchError(Exception):
    pass


def installed_apps():
    """Bilinen uygulama klasörlerindeki .app adları."""
    adlar = set()
    for klasor in APP_DIRS:
        try:
            adlar |= {yol.stem for yol in klasor.glob("*.app")}
        except OSError:
            continue
    return sorted(adlar)


def _candidates(raw):
    """Denenecek adlar: sadeleştirilmiş hâli ve ek atılmış varyantları."""
    temel = lexical.normalize(raw)
    adaylar = [temel]
    if temel:
        eksiz = _SUFFIX_RE.sub("", temel)
        if eksiz and eksiz != temel:
            adaylar.append(eksiz)
        # "chrome u" gibi ayrık kalmış tek harfli ekler ("chrome'u" → "chrome u")
        ayrik = re.sub(r"\s+\w{1,2}$", "", temel)
        if ayrik and ayrik != temel:
            adaylar.append(ayrik)
    return adaylar


def resolve_app_name(raw, apps=None):
    """Serbest yazılmış adı gerçek uygulama adına çevir; bulunamazsa girdiyi döndür."""
    adaylar = _candidates(raw)
    for aday in adaylar:
        if aday in APP_ALIASES:
            return APP_ALIASES[aday]

    kurulu = installed_apps() if apps is None else apps
    sadelesmis = {lexical.normalize(ad): ad for ad in kurulu}

    for aday in adaylar:
        if aday in sadelesmis:
            return sadelesmis[aday]

    for aday in adaylar:
        if len(aday) < 3:
            continue
        for sade, gercek in sadelesmis.items():
            if sade.startswith(aday):
                return gercek

    en_iyi, en_yuksek = None, 0.0
    for aday in adaylar:
        for sade, gercek in sadelesmis.items():
            oran = SequenceMatcher(None, aday, sade).ratio()
            if oran > en_yuksek:
                en_iyi, en_yuksek = gercek, oran
    if en_yuksek >= FUZZY_THRESHOLD:
        return en_iyi
    return raw.strip()


def _launch(app):
    proc = subprocess.run(["open", "-a", app], capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        raise AppLaunchError(f"\"{app}\" adlı uygulama bulunamadı/açılamadı.")


def closest_installed(name, apps=None, threshold=0.5):
    """Kurulu uygulamalar arasında en yakın ad; yeterince yakın değilse None."""
    kurulu = installed_apps() if apps is None else apps
    aday = lexical.normalize(name)
    en_iyi, en_yuksek = None, 0.0
    for gercek in kurulu:
        oran = SequenceMatcher(None, aday, lexical.normalize(gercek)).ratio()
        if oran > en_yuksek:
            en_iyi, en_yuksek = gercek, oran
    return en_iyi if en_yuksek >= threshold else None


def open_app(name, run_fn=None, apps=None):
    """Open a macOS app by (possibly Turkish) name. Returns the resolved app name."""
    run_fn = run_fn or _launch
    app = resolve_app_name(name, apps=apps)
    if not app:
        raise AppLaunchError("Hangi uygulamayı açacağımı anlayamadım.")
    try:
        run_fn(app)
    except AppLaunchError:
        # Kurulu olmayan bir ad: en yakın uygulamayı öner, kullanıcı el yordamıyla aramasın.
        oneri = closest_installed(name, apps=apps)
        if oneri and lexical.normalize(oneri) != lexical.normalize(app):
            raise AppLaunchError(
                f"\"{app}\" bulunamadı. Bunu mu demek istedin: {oneri}?") from None
        raise
    return app
