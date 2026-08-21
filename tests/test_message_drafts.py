"""Mail ve WhatsApp taslakları: alıcı, konu ve içerik çıkarımı."""
from app import assistant

KISILER = {
    "ahmet": [{"name": "Ahmet Yılmaz", "emails": ["ahmet@ornek.com"],
               "phones": ["+90 555 111 22 33"]}],
    "ali": [{"name": "Ali Veli", "emails": ["ali@x.com"], "phones": []},
            {"name": "Ali Can", "emails": ["alican@y.com"], "phones": []}],
    "zeynep": [],
}


def deps(**over):
    base = {
        "route": lambda q: {"tool": "mail", "action": "write"},
        "chat": lambda system, user: '{"kime": "", "konu": "", "icerik": ""}',
        "find_people": lambda ad: KISILER.get(ad.lower().strip(), []),
    }
    base.update(over)
    return base


def test_mail_draft_from_an_explicit_address():
    res = assistant.answer("ahmet@ornek.com adresine 'Toplantı' konulu mail gönder: yarın 14:00?",
                           deps=deps())
    pa = res["pending_action"]
    assert pa["type"] == "mail" and pa["to"] == "ahmet@ornek.com"
    assert pa["subject"] == "Toplantı" and "yarın 14:00" in pa["body"]


def test_mail_draft_resolves_a_name_from_contacts():
    res = assistant.answer("Ahmet'e mail gönder: yarın toplantı var", deps=deps())
    pa = res["pending_action"]
    assert pa["to"] == "ahmet@ornek.com"
    assert "Ahmet Yılmaz" in res["text"]  # kimin seçildiği kullanıcıya gösterilmeli


def test_ambiguous_contact_asks_instead_of_guessing():
    res = assistant.answer("Ali'ye mail gönder: selam", deps=deps())
    assert res["pending_action"] is None
    assert "Ali Veli" in res["text"] and "Ali Can" in res["text"]


def test_unknown_contact_asks_for_the_address():
    res = assistant.answer("Zeynep'e mail gönder: selam", deps=deps())
    assert res["pending_action"] is None
    assert "adres" in res["text"].lower()


def test_body_is_extracted_by_the_model_when_regex_fails():
    d = deps(chat=lambda system, user:
             '{"kime": "Ahmet", "konu": "Rapor", "icerik": "rapor ektedir"}')
    res = assistant.answer("Ahmet'e rapor hakkında bir mail at", deps=d)
    pa = res["pending_action"]
    assert pa["subject"] == "Rapor" and pa["body"] == "rapor ektedir"


def test_whatsapp_draft_uses_the_phone_from_contacts():
    d = deps(route=lambda q: {"tool": "whatsapp", "action": "write"})
    res = assistant.answer("Ahmet'e wp'den mesaj at: yolda mısın", deps=d)
    pa = res["pending_action"]
    assert pa["type"] == "whatsapp"
    assert pa["phone"] == "905551112233"
    assert pa["message"] == "yolda mısın"


def test_whatsapp_draft_accepts_a_written_number():
    d = deps(route=lambda q: {"tool": "whatsapp", "action": "write"})
    res = assistant.answer("0532 444 55 66 numarasına wp mesajı at: selam", deps=d)
    assert res["pending_action"]["phone"] == "905324445566"


def test_whatsapp_read_is_declined_clearly():
    d = deps(route=lambda q: {"tool": "whatsapp", "action": "read"})
    res = assistant.answer("whatsapp mesajlarımı oku", deps=d)
    assert res["pending_action"] is None
    assert "okuyamıyorum" in res["text"].lower() or "okuyamam" in res["text"].lower()


def test_confirming_whatsapp_calls_the_sender():
    yakalanan = {}
    d = deps(send_whatsapp=lambda phone, message: yakalanan.update(phone=phone, message=message))
    pa = {"type": "whatsapp", "phone": "905551112233", "message": "selam", "contact": "Ahmet"}
    mesaj = assistant.confirm(pa, deps=d)
    assert yakalanan == {"phone": "905551112233", "message": "selam"}
    assert "whatsapp" in mesaj.lower()


KISILER_TAM = {
    "ahmet": [{"name": "Ahmet Yılmaz", "emails": [], "phones": ["+90 555 111 22 33"]},
              {"name": "Ahmet Kaya", "emails": [], "phones": ["0532 444 55 66"]}],
    "ahmet yılmaz": [{"name": "Ahmet Yılmaz", "emails": [], "phones": ["+90 555 111 22 33"]}],
}


def deps_tam(**over):
    d = deps(route=lambda q: {"tool": "whatsapp", "action": "write"},
             find_people=lambda ad: KISILER_TAM.get(ad.lower().strip(), []))
    d.update(over)
    return d


def test_full_name_disambiguates():
    res = assistant.answer("Ahmet Yılmaz'a wp'den mesaj at: yoldayım", deps=deps_tam())
    assert res["pending_action"]["phone"] == "905551112233"


def test_leading_capitalised_word_does_not_break_the_lookup():
    # "Yarın Ahmet Yılmaz'a…" → önce tüm öbek, sonra baştan kelime atılarak denenir.
    res = assistant.answer("Yarın Ahmet Yılmaz'a wp'den mesaj at: buluşalım", deps=deps_tam())
    assert res["pending_action"]["phone"] == "905551112233"


def test_short_name_still_reports_ambiguity():
    res = assistant.answer("Ahmet'e wp'den mesaj at: selam", deps=deps_tam())
    assert res["pending_action"] is None
    assert "Ahmet Kaya" in res["text"]
