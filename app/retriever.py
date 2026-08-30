import re

from app import bm25, config, lexical, llm, store
from app.similarity import cosine


def score(query, text, qvec, embedding, kelime=0.0):
    """Üç sinyalin harmanı.

    kosinüs — anlamı yakalar, gündelik dille sorulan soruda işe yarar
    BM25     — ayırt edici terimi birebir yakalar ("tahliye taahhüdü")
    bulanık  — yazım hatasını affeder ("taahütü")

    Ağırlıklar ölçümle seçildi; tek başına hiçbiri yeterli değil.
    """
    return (YOGUN_AGIRLIK * cosine(qvec, embedding)
            + KELIME_AGIRLIK * kelime
            + BULANIK_AGIRLIK * lexical.fuzzy_score(query, text))


def accepts(total, dense, lex, threshold=None, kelime=0.0):
    """Parça bağlama alınsın mı.

    Eşiği geçmesi yeterli. Geçmiyorsa iki kurtarma yolu var: bulanık eşleşme
    güçlüyse (yazım hatalı ama doğru soru) ya da kelime katmanı çok emin ise
    (kanunda birebir geçen ayırt edici terim). İkincisi mevzuat korpusuyla
    geldi: kosinüs kaçırdığında doğru maddeyi yalnız BM25 buluyor.
    """
    if total >= (config.SIM_THRESHOLD if threshold is None else threshold):
        return True
    if lex >= config.LEXICAL_RESCUE and dense >= config.DENSE_FLOOR:
        return True
    return kelime >= KELIME_KURTARMA


# Sözlüksel katmanın uygulanacağı aday sayısı. Kosinüs bütün parçalar üzerinde
# ucuzdur (3.069 parçada 0,08 sn); SequenceMatcher tabanlı sözlüksel eşleşme
# pahalıdır (aynı korpusta 8,7 sn). Yazım hatası toleransı yalnızca en yakın
# adaylarda gerekli olduğu için sözlüksel katman havuzla sınırlanır.
ADAY_HAVUZU = 60

# Kelime katmanının kosinüsle harmanlanma ağırlığı. Ölçümle seçildi: yalnız
# kosinüs hit@1 2/10, yalnız BM25 2/10, 0.6/0.4 harmanı 4/10.
YOGUN_AGIRLIK = 0.5
KELIME_AGIRLIK = 0.3
BULANIK_AGIRLIK = 0.2

# Madde başlığı ayrı bir sinyaldir: kanun koyucunun yazdığı konu etiketi.
# "Dava şartları nelerdir?" sorusunun cevabı başlığı tam da "Dava şartları" olan
# maddedir, ama başlık 600 karakterlik gövdenin içinde üç kelimedir ve sinyali
# erir. Ağırlık taramayla seçildi: 0.08-0.20 aralığında hit@1 16-17/27, 0.15-0.18
# kararlı; bonussuz 15/27.
BASLIK_AGIRLIK = 0.15

# Kelime katmanı bu kadar eminse (en iyi eşleşmeye çok yakınsa) parça eşiği
# geçemese bile alınır: kanunda birebir geçen ayırt edici bir terim yakalanmıştır.
KELIME_KURTARMA = 0.85

# Ters indeks parça sayısı değişmedikçe yeniden kurulmaz (3.069 parçada 0,1 sn).
_dizin_onbellek = None
_dizin_boyut = -1
_basliklar = []


# Künyedeki "(2/5)" gibi parça işaretleri başlığın parçası değildir.
_PARCA_EKI = re.compile(r"\s*\(\d+/\d+\)\s*$")


# Başlığın puan alabilmesi için taşıması gereken en az anlamlı kelime sayısı.
# Tek kelimelik başlıklar ("Zamanı", "Şekil", "Konusu") bilgi taşımaz ve yanlış
# eşleşme üretir: "ne zaman yaptırılır" sorusu "2. Zamanı" başlıklı maddeyi
# çekip hukuk dışı soruyu reddetme yetisini bozdu.
BASLIK_ASGARI_KELIME = 2


def baslik_puani(baslik, soru):
    """Başlığın soruyla örtüşmesi. Bilgi taşımayan kısa başlıklar puan almaz."""
    kelimeler = lexical.tokens(baslik or "")
    if len(kelimeler) < BASLIK_ASGARI_KELIME:
        return 0.0
    return lexical.fuzzy_score(baslik, soru)


def basligi_ayikla(parca_metni):
    """Parçanın künyesinden madde başlığını çıkar. Başlık yoksa boş dizge."""
    ilk = (parca_metni or "").splitlines()[0] if parca_metni else ""
    if "—" not in ilk:
        return ""
    return _PARCA_EKI.sub("", ilk.split("—", 1)[1]).strip()


def _dizin(metinler):
    global _dizin_onbellek, _dizin_boyut, _basliklar
    if _dizin_onbellek is None or _dizin_boyut != len(metinler):
        _dizin_onbellek = bm25.Dizin(metinler)
        _basliklar = [basligi_ayikla(m) for m in metinler]
        _dizin_boyut = len(metinler)
    return _dizin_onbellek


def get_top_chunks(query, k=None, embed_fn=None, baslik_sorgusu=None):
    """Return up to k (source, text, score) chunks most similar to query, above threshold.

    `baslik_sorgusu`: başlık eşleşmesi bununla hesaplanır. Sorgu kanun
    terimleriyle genişletildiğinde (bkz. app/terimler.py) başlık puanı özgün
    soruya bakmalı — genişletilmiş sorguda daha çok kelime vardır ve her başlık
    daha kolay eşleşir, sinyal körelir.
    """
    k = k or config.TOP_K
    # Sorgu, belge gömme yolundan değil sorgu yolundan geçer: E5 gibi modellerde
    # ikisi farklı ön ek ister ve karıştırılırsa model yanlış işte kullanılır.
    qvec = embed_fn([query])[0] if embed_fn else llm.embed_query(query)

    # 1) İki ucuz katman, ikisi de bütün korpusu görür:
    #    kosinüs anlamı yakalar, BM25 ayırt edici terimi ("tahliye taahhüdü")
    #    birebir yakalar. Kelime katmanı yalnız kosinüsün adaylarında çalışsaydı,
    #    kosinüs kaçırdığında doğru maddeyi hiç göremezdi.
    parcalar = store.all_chunks()
    metinler = [txt for (_src, txt, _emb) in parcalar]
    kelime = _dizin(metinler).normalize(query)
    bas_sorgu = baslik_sorgusu or query
    yogun = []
    for i, (src, txt, emb) in enumerate(parcalar):
        d = cosine(qvec, emb)
        # Değişken adı `k` olamaz: fonksiyonun top-K parametresini gölgeler.
        kp = kelime.get(i, 0.0)
        bs = baslik_puani(_basliklar[i], bas_sorgu)
        yogun.append((YOGUN_AGIRLIK * d + KELIME_AGIRLIK * kp + BASLIK_AGIRLIK * bs,
                      src, txt, d, kp, bs))
    yogun.sort(key=lambda r: r[0], reverse=True)

    # 2) Pahalı katman: yalnız en yakın adaylarda bulanık sözlüksel eşleşme
    #    (yazım hatası toleransı). SequenceMatcher bütün korpusta 8,7 saniye,
    #    60 adayda görünmez.
    scored = []
    for _harman, src, txt, dense, kelime_puani, bas_puani in yogun[:ADAY_HAVUZU]:
        lex = lexical.fuzzy_score(query, txt)
        total = (YOGUN_AGIRLIK * dense + KELIME_AGIRLIK * kelime_puani
                 + BULANIK_AGIRLIK * lex + BASLIK_AGIRLIK * bas_puani)
        if accepts(total, dense, lex, kelime=kelime_puani):
            scored.append((src, txt, total))
    scored.sort(key=lambda r: r[2], reverse=True)
    return scored[:k]
