"""Mevzuat yanıtı: cevap üretmez, madde metninden çıkarır.

Ölçüm şunu gösterdi: bu boyuttaki yerel modeller Türkçe hukuk metninde yanlış
cümleler kuruyor ("arabulucuya gitmek zorunlu değildir" gibi — yanlış). Hukukta
uydurulmuş bir cümle, cevapsızlıktan beterdir; kaynak gösterildiği için
doğrulanmış izlenimi verir.

Bu yüzden buradaki yanıt tamamen çıkarımsaldır: getirilen maddenin kendi
cümlelerinden soruya en yakın olanı seçilir ve öne alınır. Ekranda görünen her
kelime kanun metnindendir; tek kelime üretilmez.

Kullanıcı 3.069 maddelik yığından beş maddeye, oradan da tek cümleye iner —
kazanç budur.
"""
import re
from dataclasses import dataclass, field

from app import lexical

# Cümle sonu: nokta/soru/ünlem + boşluk. Fıkra numaraları "(1)" cümle başı sayılır.
_CUMLE_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Aday:
    atif: str
    baslik: str
    metin: str
    puan: float
    one_cikan: str = ""


@dataclass
class Yanit:
    birincil: Aday = None
    digerleri: list = field(default_factory=list)
    bulunamadi: bool = False
    tavsiye_reddi: bool = False
    mesaj: str = ""


def _ayikla(parca_metni):
    """Parçayı (atıf, başlık, madde metni) olarak ayır.

    Parçanın ilk satırı ingest sırasında yazılan künyedir:
    "6502 sayılı ... md. 48 — Mesafeli sözleşmeler"
    """
    satirlar = parca_metni.split("\n\n", 1)
    kunye = satirlar[0].strip()
    govde = satirlar[1].strip() if len(satirlar) > 1 else ""
    if "—" in kunye:
        atif, baslik = kunye.split("—", 1)
    else:
        atif, baslik = kunye, ""
    # Bölünmüş maddelerde künyede "(2/5)" gibi bir ek olur; atıf madde düzeyindedir.
    _EK = r"\s*\(\d+/\d+\)\s*$"
    # PDF'ten gelen metin rastgele satır sonları taşır. Boşluklar burada
    # sadeleştirilir ki gösterilen metin ile çıkarılan cümle aynı biçimde olsun —
    # aksi hâlde vurgulama hiç eşleşmez. Kelimeler değişmez, yalnız boşluk.
    return (re.sub(_EK, "", atif.strip()),
            re.sub(_EK, "", baslik.strip()),
            " ".join(govde.split()))


def cumleler(metin):
    """Madde metnini cümlelere ayır. Metin birebir korunur."""
    duz = " ".join((metin or "").split())
    return [c.strip() for c in _CUMLE_RE.split(duz) if c.strip()]


def en_yakin_cumle(soru, metin):
    """Soruyla en çok örtüşen cümle. Üretim yok, seçim var."""
    adaylar = cumleler(metin)
    if not adaylar:
        return ""
    return max(adaylar, key=lambda c: lexical.fuzzy_score(soru, c))


def hazirla(soru, parcalar):
    """`parcalar`: erişimden gelen (parça metni, puan) listesi — alaka sırasıyla.

    Aynı maddenin farklı bölümleri tek adayda birleştirilir. Uzun bir madde dokuz
    parçaya bölünmüşse listenin beş sırasını ona harcamak, kullanıcıya beş ayrı
    madde göstermek yerine aynı maddeyi beş kez göstermek olurdu.
    """
    if not parcalar:
        return Yanit(bulunamadi=True)

    birlesik = {}   # atıf → Aday (ilk görülen sıra korunur: alaka sırası)
    for metin, puan in parcalar:
        atif, baslik, govde = _ayikla(metin)
        varolan = birlesik.get(atif)
        if varolan is None:
            birlesik[atif] = Aday(atif=atif, baslik=baslik, metin=govde, puan=puan)
        else:
            varolan.metin = f"{varolan.metin}\n\n{govde}".strip()
            varolan.puan = max(varolan.puan, puan)

    adaylar = list(birlesik.values())
    for a in adaylar:
        a.one_cikan = en_yakin_cumle(soru, a.metin)
    return Yanit(birincil=adaylar[0], digerleri=adaylar[1:])


def sor(soru, k=None):
    """Soruyu erişime verip aday maddeleri hazırlar. Dil modeli çağrılmaz.

    Tahmin ya da tavsiye isteyen sorularda madde gösterilmez: bir madde listesi
    "davayı kazanır mıyım" sorusunu cevaplamaz, ama cevapladığı izlenimini
    yaratır.
    """
    from app import config, hukuki_kapsam, retriever
    if hukuki_kapsam.tavsiye_istiyor(soru):
        return Yanit(tavsiye_reddi=True, mesaj=hukuki_kapsam.MESAJ)
    parcalar = retriever.get_top_chunks(soru, k=k or config.TOP_K)
    # retriever (kaynak, metin, puan) döndürür; burada kaynak değil metin gerekli.
    return hazirla(soru, [(p[-2], p[-1]) if len(p) == 3 else p for p in parcalar])
