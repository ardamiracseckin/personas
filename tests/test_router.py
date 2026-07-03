from app.router import route


def test_calendar_read():
    assert route("Bugün takvimimde ne var?") == {"tool": "calendar", "action": "read"}


def test_calendar_write():
    assert route("Yarın 15:00 dişçi randevusu ekle") == {"tool": "calendar", "action": "write"}


def test_mail_read():
    assert route("Okunmamış maillerim neler?") == {"tool": "mail", "action": "read"}


def test_mail_write():
    assert route("Ahmet'e bir mail gönder") == {"tool": "mail", "action": "write"}


def test_defaults_to_documents():
    assert route("Kireç temizliği nasıl yapılır?") == {"tool": "documents", "action": "read"}
