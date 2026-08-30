"""Kapsam denetimi: tahmin ve tavsiye isteyen soruları reddeder.

Projenin karakteristik kararı: asistan yorum yapmaz, maddeyi gösterir.

"Bu davayı kazanır mıyım", "ne yapmalıyım", "ne kadar tazminat alırım" gibi
sorular hukuki tavsiye ister. Bunlara madde listesi göstermek, kullanıcının
aradığı cevabı verdiği izlenimini yaratır — oysa sonuç somut olaya, delile ve
mahkemenin takdirine bağlıdır; bir madde listesi bunu söyleyemez.

Ölçüm kuralın gerekliliğini gösterdi: kural yokken beş tahmin sorusunun dördüne
madde listesi çıkıyordu.

Dedektör dar tutulur. Yanlış pozitif, gerçek bir bilgi sorusunu reddetmek
demektir ve bu, tavsiye vermekten daha sık zarar verir: "İhbar süresi ne
kadardır?" kanunda yazan bir bilgidir, "Ne kadar tazminat alırım?" değildir.
"""
import re

# İki bileşen aranır: birinci şahıs bir sonuç beklentisi ("alır mıyım",
# "kazanır mıyım") ya da doğrudan tavsiye isteği ("ne yapmalıyım", "önerirsin").
_TAVSIYE = re.compile(
    r"\bne\s+yapmalı(yım|yız)\b"
    r"|\bne\s+yapabilirim\b"
    r"|\b(öneri(n|niz)?\s+ne|ne\s+önerirsin|bana\s+ne\s+önerir)"
    r"|\bsence\b"
    r"|\bhaklı\s+mıyım\b"
    r"|\bhaklı\s+çıkar\s+mıyım\b"
    r"|\bdava\s+aç(malı|sam)\b"
    r"|\bsen\s+halledebilir\b"
    r"|\bavukat\s+tut(mama|maya)\b",
    re.IGNORECASE)

# Sonuç tahmini. Kalıbı fiile bakmadan yakalamak yanlıştı: "Verilerimin
# silinmesini isteyebilir miyim?" de aynı biçimdedir ama meşru bir bilgi
# sorusudur (KVKK md. 7 cevaplıyor). Bu yüzden yalnızca sonuç bildiren fiiller
# aranır — kazanmak, kaybetmek, haklı çıkmak, sonuç/tazminat almak.
_SONUC = re.compile(
    r"\bkazan(ır|abilir|acak)\s*mı"
    r"|\bkaybed(er|ebilir)\s*mi"
    r"|\bhaklı\s+(çıkar|olur)\s*mu"
    r"|\b(sonuç|tazminat|para)\s+al(ır|abilir)\s*mı",
    re.IGNORECASE)

# Kişiselleştirilmiş miktar sorusu: "benim durumumda ne kadar", "ne kadar alırım".
_MIKTAR = re.compile(r"\bbenim\s+durumumda\b|\bne\s+kadar\s+\w+[ıiuü]rım\b", re.IGNORECASE)

MESAJ = ("Bu soru somut olaya, delillere ve mahkemenin takdirine bağlı; kanun metni tek başına "
         "cevaplayamaz ve ben tahmin yürütmüyorum. Yapabileceğim şey, durumunla ilgili maddeyi "
         "bulup önüne koymak — hangi kuralın işlediğini bilerek avukatına gidersen görüşme çok "
         "daha verimli olur. Sorunu \"hangi kural geçerli\" biçiminde sorarsan ilgili maddeleri "
         "gösterebilirim.")


def tavsiye_istiyor(soru):
    """Soru hukuki tavsiye ya da sonuç tahmini mi istiyor?"""
    metin = soru or ""
    return bool(_TAVSIYE.search(metin) or _SONUC.search(metin) or _MIKTAR.search(metin))
