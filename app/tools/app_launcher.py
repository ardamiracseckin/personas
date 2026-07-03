import subprocess


class AppLaunchError(Exception):
    pass


# Yaygın Türkçe adlar → gerçek macOS uygulama adları.
APP_ALIASES = {
    "not defteri": "Notes", "notlar": "Notes",
    "hesap makinesi": "Calculator", "hesap makinası": "Calculator",
    "ayarlar": "System Settings", "sistem ayarları": "System Settings",
    "safari": "Safari",
    "chrome": "Google Chrome", "google chrome": "Google Chrome",
    "spotify": "Spotify", "müzik": "Music", "muzik": "Music",
    "takvim": "Calendar", "mail": "Mail", "posta": "Mail",
    "mesajlar": "Messages", "terminal": "Terminal",
    "fotoğraflar": "Photos", "fotograflar": "Photos",
    "kod": "Visual Studio Code", "vscode": "Visual Studio Code",
    "whatsapp": "WhatsApp", "telegram": "Telegram", "discord": "Discord",
    "haritalar": "Maps", "hava durumu": "Weather", "saat": "Clock",
    "önizleme": "Preview", "onizleme": "Preview",
}


def resolve_app_name(raw):
    return APP_ALIASES.get(raw.strip().lower(), raw.strip())


def _launch(app):
    proc = subprocess.run(["open", "-a", app], capture_output=True, text=True, timeout=15)
    if proc.returncode != 0:
        raise AppLaunchError(f"\"{app}\" adlı uygulama bulunamadı/açılamadı.")


def open_app(name, run_fn=None):
    """Open a macOS app by (possibly Turkish) name. Returns the resolved app name."""
    run_fn = run_fn or _launch
    app = resolve_app_name(name)
    if not app:
        raise AppLaunchError("Hangi uygulamayı açacağımı anlayamadım.")
    run_fn(app)
    return app
