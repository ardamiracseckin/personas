"""Gövde bazlı BM25 — kelime düzeyinde erişim katmanı.

Kanun metninde ayırt edici terimler birebir geçer ("tahliye taahhüdü", "cayma
hakkı", "dava şartı"). Embedding araması bunları kaçırabiliyor çünkü kullanıcı
gündelik dille soruyor; kelime araması ise Türkçenin ekleri yüzünden tutmuyor:
sorguda "taahhüdü", metinde "taahhüdünde".

Çözüm gövde: kelimeler ilk beş karaktere indirilerek eşleştirilir. Ölçüm bu
sayıyı seçti — tam kelimeyle hit@1 1/10, gövdeyle 2/10, kosinüsle harmanlanınca
4/10 (kosinüs tek başına 2/10).

Dizin kurulumu 3.069 parçada 0,1 saniye, sorgu maliyeti ölçülemeyecek kadar
küçük; ters indeks sayesinde yalnız sorgudaki terimlerin belgeleri gezilir.
"""
import math
from collections import Counter, defaultdict

from app import lexical

GOVDE = 5      # ölçümle seçildi

# Puanlar bu değere bölünerek 0-1 aralığına çekilir. Sorgu içi maksimuma bölmek
# yanlıştı: alakasız bir soruda bile en iyi parça 1.0 alıyor ve asistanın
# "bilmiyorum" diyebilmesi kırılıyordu. Ölçüm ham puanları ayırt edilebilir
# buldu — konuyla ilgili sorularda 10-19, alakasızlarda 7-9,6 — bu yüzden
# mutlak büyüklüğü koruyan sabit bir doyum değeri kullanılır.
DOYUM = 20.0
K1 = 1.5       # terim doygunluğu (standart BM25 değeri)
B = 0.75       # uzunluk düzeltmesi (standart BM25 değeri)


def govdele(kelime):
    return kelime[:GOVDE]


class Dizin:
    """Bir metin kümesi üzerinde BM25 ters indeksi."""

    def __init__(self, belgeler):
        self.n = len(belgeler)
        sayimlar = [Counter(govdele(k) for k in lexical.tokens(b)) for b in belgeler]
        self.uzunluk = [sum(c.values()) for c in sayimlar]
        self.ortalama = (sum(self.uzunluk) / self.n) if self.n else 0.0
        df = Counter()
        for c in sayimlar:
            df.update(c.keys())
        self.idf = {t: math.log(1 + (self.n - adet + 0.5) / (adet + 0.5))
                    for t, adet in df.items()}
        self.ters = defaultdict(list)
        for i, c in enumerate(sayimlar):
            for t, f in c.items():
                self.ters[t].append((i, f))

    def puanla(self, sorgu):
        """{belge sırası: BM25 puanı}. Eşleşmeyen belge sözlükte yer almaz."""
        puan = defaultdict(float)
        for terim in (govdele(k) for k in lexical.tokens(sorgu)):
            if terim not in self.ters:
                continue
            idf = self.idf[terim]
            for i, f in self.ters[terim]:
                pay = f * (K1 + 1)
                payda = f + K1 * (1 - B + B * self.uzunluk[i] / self.ortalama)
                puan[i] += idf * pay / payda
        return dict(puan)

    def normalize(self, sorgu):
        """Puanları sabit doyuma bölerek 0–1 aralığına çek.

        Kosinüsle harmanlanabilmesi için gerekli: BM25 puanı sınırsızdır,
        kosinüs 0–1 arasındadır. Doyum sabittir, sorguya göre değişmez —
        böylece "hiçbir parça iyi eşleşmedi" durumu ölçülebilir kalır.
        """
        return {i: min(1.0, p / DOYUM) for i, p in self.puanla(sorgu).items()}
