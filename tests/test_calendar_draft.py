"""Takvim taslağı üretimi: tarih/saat ifadeleri doğru çözülmeli, başlığa sızmamalı.

Referans an her testte sabit: 20 Ağustos 2026, Perşembe, saat 10:00.
"""
from datetime import datetime

import pytest

from app.assistant import _parse_calendar_draft

NOW = datetime(2026, 8, 20, 10, 0)  # perşembe


def draft(text):
    return _parse_calendar_draft(text, now=NOW)


@pytest.mark.parametrize("text,expected", [
    ("Bugün 14:00 toplantı ekle", (2026, 8, 20)),
    ("Yarın 15:00 dişçi randevusu ekle", (2026, 8, 21)),
    ("Öbür gün 10:00 toplantı ekle", (2026, 8, 22)),
    ("3 gün sonra 09:00 kontrol ekle", (2026, 8, 23)),
    ("Haftaya 11:00 sunum ekle", (2026, 8, 27)),
    ("Pazartesi 14:00 vize ekle", (2026, 8, 24)),
    ("Cuma 09:00 spor ekle", (2026, 8, 21)),
    ("25 Ağustos 09:30 vize sınavı ekle", (2026, 8, 25)),
])
def test_dates_are_resolved(text, expected):
    d = draft(text)
    assert (d["year"], d["month"], d["day"]) == expected


def test_same_weekday_later_today_stays_today():
    d = draft("Perşembe 18:00 antrenman ekle")
    assert (d["month"], d["day"], d["hour"]) == (8, 20, 18)


def test_same_weekday_already_passed_goes_next_week():
    d = draft("Perşembe 08:00 antrenman ekle")
    assert (d["month"], d["day"]) == (8, 27)


@pytest.mark.parametrize("text,hour,minute", [
    ("Yarın 15:00 dişçi ekle", 15, 0),
    ("Yarın 15.30 dişçi ekle", 15, 30),
    ("Yarın saat 9 dişçi ekle", 9, 0),
    ("Yarın sabah dişçi ekle", 9, 0),
    ("Yarın öğlen dişçi ekle", 12, 0),
    ("Yarın akşam dişçi ekle", 19, 0),
])
def test_times_are_resolved(text, hour, minute):
    d = draft(text)
    assert (d["hour"], d["minute"]) == (hour, minute)


# Başlık kullanıcının kelimeleriyle kalır; yalnızca tarih/saat ifadeleri ve emir
# kipindeki fiiller atılır ("diş randevusu" bilgi taşır, "randevu" da atılmamalı).
@pytest.mark.parametrize("text,expected", [
    ("Perşembe 14:00 diş randevusu ekle", "diş randevusu"),
    ("25 Ağustos 09:30 vize sınavı ekle", "vize sınavı"),
    ("Öbür gün 10:00 ekip toplantısı oluştur", "ekip toplantısı"),
    ("Yarın sabah spor salonu etkinliği ekle", "spor salonu etkinliği"),
    ("Yarın 14:00 2 saatlik atölye ekle", "atölye"),
    ("Cumartesi 11:00 kuaför randevusu lütfen ekle", "kuaför randevusu"),
])
def test_date_expressions_do_not_leak_into_the_title(text, expected):
    assert draft(text)["title"] == expected


def test_duration_is_parsed():
    assert draft("Yarın 14:00 2 saatlik atölye ekle")["duration_min"] == 120
    assert draft("Yarın 14:00 45 dakikalık görüşme ekle")["duration_min"] == 45
    assert draft("Yarın 14:00 görüşme ekle")["duration_min"] == 60


def test_untitled_event_gets_a_default():
    assert draft("Yarın 14:00 ekle")["title"] == "Etkinlik"
