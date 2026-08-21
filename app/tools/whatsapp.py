"""WhatsApp'a mesaj gönderme.

İki kip var. Varsayılan **taslak**: sohbet, mesaj yazılmış hâlde açılır ve
gönder tuşuna kullanıcı basar — ek izin istemez, yanlış kişiye gitme riski
yoktur. `config.WHATSAPP_AUTO_SEND` açıksa taslak açıldıktan sonra Enter
tuşlanır; bu, macOS Erişilebilirlik izni ister ve WhatsApp arayüzü değişirse
bozulabilir.
"""
import re
import subprocess
import time
from urllib.parse import quote

from app import config

MIN_DIGITS = 7
AUTO_SEND_DELAY = 3.0  # sohbetin açılıp odaklanması için beklenen süre

_KEYSTROKE = 'tell application "System Events" to keystroke return'


class WhatsAppError(Exception):
    pass


def normalize_phone(raw, country_code=None):
    """Serbest yazılmış numarayı whatsapp:// için sadeleştir: yalnızca rakamlar."""
    country_code = country_code or config.DEFAULT_COUNTRY_CODE
    metin = (raw or "").strip()
    uluslararasi = metin.startswith("+")
    rakamlar = re.sub(r"\D", "", metin)
    if len(rakamlar) < MIN_DIGITS:
        raise ValueError(f"Telefon numarası anlaşılamadı: {raw!r}")
    if uluslararasi:
        return rakamlar
    rakamlar = rakamlar.lstrip("0")
    if not rakamlar.startswith(country_code):
        rakamlar = country_code + rakamlar
    return rakamlar


def draft_url(phone, text):
    return f"whatsapp://send?phone={phone}&text={quote(text or '', safe='')}"


def _open(url):
    proc = subprocess.run(["open", url], capture_output=True, text=True, timeout=20)
    if proc.returncode != 0:
        raise WhatsAppError("WhatsApp açılamadı. Uygulama kurulu mu?")


def _press_return():
    subprocess.run(["osascript", "-e", _KEYSTROKE], capture_output=True, text=True, timeout=20)


def send(phone, text, auto=None, open_fn=None, keystroke_fn=None, sleep_fn=None):
    """Mesajı WhatsApp'ta hazırla. auto=True ise gönderme tuşuna da basar."""
    auto = config.WHATSAPP_AUTO_SEND if auto is None else auto
    open_fn = open_fn or _open
    keystroke_fn = keystroke_fn or _press_return
    sleep_fn = sleep_fn or time.sleep

    numara = normalize_phone(phone)
    open_fn(draft_url(numara, text))
    if auto:
        sleep_fn(AUTO_SEND_DELAY)
        keystroke_fn()
    return numara
