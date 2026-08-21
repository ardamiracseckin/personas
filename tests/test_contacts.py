"""Rehber araması: isimden e-posta ve telefon bulma."""
from app.tools import contacts

CIKTI = (
    "Ahmet Yılmaz|ahmet@ornek.com;ahmet.yilmaz@is.com|+90 555 111 22 33;\n"
    "Ahmet Kaya||0532 444 55 66;\n"
    "Mehmet Demir|mehmet@ornek.com|\n"
)


def test_parses_people():
    kisiler = contacts.parse_people(CIKTI)
    assert [k["name"] for k in kisiler] == ["Ahmet Yılmaz", "Ahmet Kaya", "Mehmet Demir"]
    assert kisiler[0]["emails"] == ["ahmet@ornek.com", "ahmet.yilmaz@is.com"]
    assert kisiler[0]["phones"] == ["+90 555 111 22 33"]
    assert kisiler[1]["emails"] == []


def test_find_uses_the_script_and_filters_empty_lines():
    kisiler = contacts.find_people("ahmet", run_fn=lambda script: CIKTI)
    assert len(kisiler) == 3


def test_with_email_and_with_phone_filters():
    kisiler = contacts.parse_people(CIKTI)
    assert [k["name"] for k in contacts.with_email(kisiler)] == ["Ahmet Yılmaz", "Mehmet Demir"]
    assert [k["name"] for k in contacts.with_phone(kisiler)] == ["Ahmet Yılmaz", "Ahmet Kaya"]


def test_name_is_escaped_in_the_script():
    yakalanan = {}
    contacts.find_people('Ahmet "Ali"', run_fn=lambda s: yakalanan.setdefault("s", s) or "")
    assert '"Ahmet ' in yakalanan["s"]
    assert yakalanan["s"].count('"') % 2 == 0  # tırnaklar dengeli, script bozulmadı
