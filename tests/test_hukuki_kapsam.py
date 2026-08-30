"""Kapsam denetimi: tahmin ve tavsiye isteyen sorular reddedilir.

Projenin karakteristik kararı: asistan yorum yapmaz, maddeyi gösterir. "Bu
davayı kazanır mıyım", "ne yapmalıyım", "ne kadar tazminat alırım" gibi sorular
hukuki tavsiye ister; bunlara madde göstermek, kullanıcının aradığı cevabı
verdiği izlenimi yaratır. Oysa sonuç somut olaya, delile ve mahkemenin takdirine
bağlıdır — bir madde listesi bunu söyleyemez.

Ölçüm bu kuralın gerekliliğini gösterdi: kural yokken beş tahmin sorusunun
dördüne madde listesi çıkıyordu.

Dedektör dar tutulur: yanlış pozitif, gerçek bir bilgi sorusunu reddetmek
demektir ve bu daha kötüdür.
"""
import json
from pathlib import Path

from app import hukuki_kapsam

SORULAR = json.loads(
    (Path(__file__).resolve().parent.parent / "eval" / "mevzuat_sorular.json")
    .read_text(encoding="utf-8"))["questions"]


def kategori(ad):
    return [s["question"] for s in SORULAR if s["category"] == ad]


def test_every_prediction_question_is_caught():
    for soru in kategori("tahmin"):
        assert hukuki_kapsam.tavsiye_istiyor(soru), soru


def test_no_information_question_is_refused():
    for soru in kategori("cevaplanabilir"):
        assert not hukuki_kapsam.tavsiye_istiyor(soru), soru


def test_offtopic_and_edge_questions_are_not_flagged():
    for soru in kategori("cevaplanamaz") + kategori("uc_durum"):
        assert not hukuki_kapsam.tavsiye_istiyor(soru), soru


def test_common_phrasings_of_asking_for_advice():
    for soru in ["Ne yapmalıyım?", "Dava açsam kazanır mıyım",
                 "Bu durumda haklı çıkar mıyım?", "Bana ne önerirsin",
                 "Şikayet etsem sonuç alır mıyım?"]:
        assert hukuki_kapsam.tavsiye_istiyor(soru), soru


def test_information_questions_that_look_similar_are_not_flagged():
    # "Ne kadar" bir bilgi sorusu da olabilir: kanunda yazan süre sorulmaktadır.
    for soru in ["İhbar süresi ne kadardır?", "Kira artış oranı ne kadar olabilir?",
                 "Yıllık izin kaç gündür?"]:
        assert not hukuki_kapsam.tavsiye_istiyor(soru), soru


def test_the_message_says_what_the_assistant_does_instead():
    assert "madde" in hukuki_kapsam.MESAJ.lower()
    assert "avukat" in hukuki_kapsam.MESAJ.lower()
