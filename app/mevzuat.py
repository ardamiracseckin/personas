"""Kanun metnini madde bazlı parçalar.

Hukukta atıf kaynağın kendisidir: "İş Kanunu md. 17" demek ile "bir yerde
okudum" demek arasındaki fark, kullanıcının hakkını arayıp arayamamasıdır. Bu
yüzden parçalama birimi paragraf değil **madde**dir; her parça kendi kanun ve
madde numarasını taşır ve metin birebir korunur.

İki resmî yazım biçimi vardır ve ikisi de karşımıza çıkıyor:

    Madde 12 –      (2011 öncesi kanunlar: 2918, 4721, 4857)
    MADDE 12- (1)   (2011 sonrası kanunlar: 6098, 6100, 6502, 6698, 7036)

Değişiklik ibareleri ("(Değişik:2/3/2024-7499/33 md.)", "(Mülga:...)")
silinmez: maddenin hangi tarihli hâli olduğunu ve hangi fıkranın yürürlükten
kalktığını yalnızca onlar söyler.
"""
import re
from dataclasses import dataclass

# Madde başlangıcı: satır başında MADDE/Madde + numara + ayraç.
# Numaradan sonra "/A" gibi ek harfler olabilir (mükerrer maddeler).
_MADDE_RE = re.compile(
    r"^[ \t]*(?P<on>Ek|EK|Geçici|GEÇİCİ|Mükerrer)?\s*"
    r"(?P<etiket>MADDE|Madde)\s*(?P<no>\d+(?:/[A-ZÇĞİÖŞÜ])?)\s*(?P<ayrac>[-–—])",
    re.MULTILINE)

# Ek ve geçici maddeler ayrı numara dizisi kullanır: "Geçici Madde 3" ile
# "Madde 3" bambaşka hükümlerdir ve atıfta karıştırılmaları hak kaybı doğurur.
_ON_EK = {"ek": "Ek", "geçici": "Geçici", "mükerrer": "Mükerrer"}

_KANUN_NO_RE = re.compile(r"Kanun\s*Numaras[ıi]\s*:?\s*(\d+)")
_KABUL_RE = re.compile(r"Kabul\s*Tarihi\s*:?\s*([\d./]+)")


@dataclass(frozen=True)
class KanunBilgisi:
    ad: str
    numara: str
    kabul: str


@dataclass(frozen=True)
class Madde:
    numara: str
    baslik: str
    metin: str


@dataclass(frozen=True)
class Parca:
    """Veritabanına yazılacak birim.

    Uzun maddeler birden fazla parçaya bölünür; hepsi aynı maddeye atıf yapar,
    `parca_no` kaçıncı bölüm olduğunu söyler.
    """
    kanun_ad: str
    kanun_no: str
    madde: str
    baslik: str
    metin: str
    parca_no: int = 1
    parca_adet: int = 1

    @property
    def atif(self):
        return f"{self.kanun_no} sayılı {self.kanun_ad} md. {self.madde}"


def kanun_bilgisi(text):
    """Metnin başındaki künyeden kanun adı, numarası ve kabul tarihi."""
    no = _KANUN_NO_RE.search(text or "")
    kabul = _KABUL_RE.search(text or "")
    ad = ""
    for satir in (text or "").splitlines():
        temiz = " ".join(satir.split())
        if temiz and not _KANUN_NO_RE.search(temiz):
            # Künye satırlarındaki dipnot numaraları ("KANUNU123") temizlenir.
            ad = re.sub(r"\d+$", "", temiz).strip()
            break
        if temiz:
            break
    return KanunBilgisi(ad=ad, numara=no.group(1) if no else "",
                        kabul=kabul.group(1) if kabul else "")


def _baslik_bul(onceki_metin):
    """Madde başlığı, madde satırının hemen üstündeki kısa satırdır."""
    for satir in reversed(onceki_metin.splitlines()):
        temiz = " ".join(satir.split())
        if not temiz:
            continue
        # Başlık kısa ve cümle değildir; uzun satır önceki maddenin gövdesidir.
        if len(temiz) <= 90 and not temiz.endswith("."):
            return temiz
        return ""
    return ""


def maddeleri_ayir(text):
    """Metni maddelere böl. Metin birebir korunur."""
    metin = text or ""
    eslesmeler = list(_MADDE_RE.finditer(metin))
    maddeler = []
    for i, m in enumerate(eslesmeler):
        bas = m.start()
        son = eslesmeler[i + 1].start() if i + 1 < len(eslesmeler) else len(metin)
        govde = metin[bas:son].strip()
        # Küçültme Türkçe kurallarıyla yapılmalı: "GEÇİCİ".lower() Python'da
        # "geçi̇ci̇" verir ve arama tutmaz. Bu hata geçici maddeyi normal madde
        # gibi numaralandırıyordu.
        on = turkce_kucult(m.group("on") or "")
        numara = f"{_ON_EK[on]} {m.group('no')}" if on in _ON_EK else m.group("no")
        maddeler.append(Madde(numara=numara,
                              baslik=_baslik_bul(metin[:bas]),
                              metin=govde))
    return maddeler


# Bir maddenin tek parçada kalabileceği üst sınır. Kanunlarda tek maddenin
# sayfalarca sürdüğü oluyor (2918 md. 135 gibi); o boyutta bir parça hem
# embedding'e sığmaz hem de isteme eklendiğinde ilgisiz metinle bağlamı boğar.
MAX_PARCA = 1200

# Fıkra sınırı: "(1)", "(2)"… Bölme burada yapılır ki parça yarım cümleyle
# başlamasın.
_FIKRA_RE = re.compile(r"(?=\(\d{1,2}\)\s)")


def _bol(metin, max_chars):
    """Uzun maddeyi fıkra sınırlarından, gerekirse cümleden böl."""
    if len(metin) <= max_chars:
        return [metin]
    adaylar = [p for p in _FIKRA_RE.split(metin) if p.strip()]
    if len(adaylar) == 1:
        adaylar = re.split(r"(?<=\.)\s+", metin)
    kesitler, birikim = [], ""
    for aday in adaylar:
        yeni = f"{birikim} {aday}".strip() if birikim else aday.strip()
        if len(yeni) <= max_chars or not birikim:
            birikim = yeni
        else:
            kesitler.append(birikim)
            birikim = aday.strip()
        while len(birikim) > max_chars:      # tek fıkra bile sınırı aşabiliyor
            kesitler.append(birikim[:max_chars])
            birikim = birikim[max_chars:]
    if birikim:
        kesitler.append(birikim)
    return kesitler


def parcala(text, dosya="", max_chars=MAX_PARCA):
    """Kanun metnini veritabanına yazılabilir parçalara çevir."""
    bilgi = kanun_bilgisi(text)
    parcalar = []
    for m in maddeleri_ayir(text):
        kesitler = _bol(m.metin, max_chars)
        for i, kesit in enumerate(kesitler, start=1):
            parcalar.append(Parca(kanun_ad=bilgi.ad, kanun_no=bilgi.numara,
                                  madde=m.numara, baslik=m.baslik, metin=kesit,
                                  parca_no=i, parca_adet=len(kesitler)))
    return parcalar


# --- Türkçe başlık ----------------------------------------------------------
#
# Python'un .title() metodu Türkçe bilmez: "İ".lower() birleşik nokta üretir
# ("i̇"), "I".lower() ise "ı" değil "i" verir. Kanun adları bu yüzden
# "Trafi̇k", "Korunmasi" gibi bozuk çıkıyordu.

_BUYUK_KUCUK = str.maketrans("İIÇĞÖŞÜ", "iıçğöşü")
_KUCUK_BUYUK = str.maketrans("iıçğöşü", "İIÇĞÖŞÜ")


def turkce_kucult(metin):
    return (metin or "").translate(_BUYUK_KUCUK).lower()


def turkce_baslik(metin):
    """Her kelimenin ilk harfi büyük — Türkçe kurallarına göre."""
    kelimeler = []
    for kelime in (metin or "").split():
        kucuk = turkce_kucult(kelime)
        if not kucuk:
            continue
        kelimeler.append(kucuk[0].translate(_KUCUK_BUYUK).upper() + kucuk[1:])
    return " ".join(kelimeler)
