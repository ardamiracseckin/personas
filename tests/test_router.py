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


def test_app_open():
    assert route("Spotify aç") == {"tool": "app", "action": "open"}


def test_aciklama_is_not_app_open():
    # "açıkla" tam kelime "aç" içermez; belge sorusu olarak kalmalı.
    assert route("Bunu bana açıkla")["tool"] == "documents"


# --- araç önceliği: takvim kelimeleri mail isteğini kaçırmamalı -------------

def test_mail_wins_when_subject_mentions_a_meeting():
    # "toplantı" bir mailin konusu olabilir; e-posta adresi + "mail" güçlü sinyaldir.
    assert route("ali@example.com adresine toplantı hakkında mail gönder") == {
        "tool": "mail", "action": "write"}


def test_mail_wins_over_temporal_word():
    assert route("Ahmet'e yarınki sunum için mail at") == {"tool": "mail", "action": "write"}


def test_calendar_still_wins_when_signals_are_calendar_specific():
    assert route("Bugünkü toplantıyı takvime ekle") == {"tool": "calendar", "action": "write"}


def test_yaz_is_a_write_verb_for_mail():
    assert route("Ahmet'e bir mail yaz") == {"tool": "mail", "action": "write"}


def test_yazilim_does_not_trigger_write():
    # "yazılım" içindeki "yaz" yazma niyeti sayılmamalı.
    assert route("Yazılım toplantısı takvimimde var mı?") == {
        "tool": "calendar", "action": "read"}


def test_at_only_matches_as_a_whole_word():
    # "atla" veya "sanat" yazma niyeti tetiklememeli.
    assert route("Sanat etkinliği takvimimde var mı?") == {"tool": "calendar", "action": "read"}


# --- WhatsApp: mesaj göndermek ile uygulamayı açmak ayrılmalı -----------------

def test_whatsapp_message_is_a_write():
    assert route("Ahmet'e wp'den mesaj at") == {"tool": "whatsapp", "action": "write"}
    assert route("whatsapp'tan anneme mesaj gönder") == {"tool": "whatsapp", "action": "write"}


def test_opening_whatsapp_is_still_the_app_tool():
    assert route("wp aç") == {"tool": "app", "action": "open"}
    assert route("whatsappı aç") == {"tool": "app", "action": "open"}


def test_whatsapp_read_is_recognised_separately():
    assert route("whatsapp mesajlarımı oku") == {"tool": "whatsapp", "action": "read"}


def test_mail_is_unaffected():
    assert route("ali@x.com adresine mail gönder") == {"tool": "mail", "action": "write"}
