"""Gündelik dil → kanun terimi sözlüğü.

Ölçüm defalarca aynı şeyi gösterdi: kullanıcı "tahliye" diyor, kanun
"kiralananı boşaltma" diyor; kullanıcı "ev sahibi" diyor, kanun "kiraya veren"
diyor; kullanıcı "bozuk ürün" diyor, kanun "ayıplı mal" diyor. Aynı sorular
kanun diliyle sorulduğunda isabet ikiye katlanıyordu (hit@1 2/10 → 5/10).

Bu çeviriyi modele yaptırmak denendi ve ölçümde battı: `qwen3.5-2b-text` terim
üretmek yerine soruyu cevaplamaya kalkıp yanlış cümleler kurdu ("arabulucuya
gitmek zorunlu değildir"), `phi-4-mini` anlamsız kelimeler yazdı. Onun yerine
elle kurulmuş, dar bir sözlük kullanılıyor.

İki kural:

1. **Hiçbir terim uydurulmaz.** Sözlükteki her kanun terimi korpusta birebir
   geçer; bir test bunu her koşumda doğrular.
2. **Madde başlığına değil, sözcük dağarcığına eşlenir.** İlk sürümde
   "verilerim" → "ilgili kişinin hakları" yazıyordu; o bir maddenin (KVKK md. 11)
   başlığıdır ve bütün KVKK sorularını o maddeye çekiyordu — oysa "nasıl
   başvururum" sorusunun cevabı md. 13'tür. Genel terim ("kişisel veri", "veri
   sorumlusu") sorunun kendi ayrıntısının konuşmasına izin verir.
3. **Sorunun kendisi korunur.** Terimler eklenir, kullanıcının kelimeleri
   silinmez — genişletme yanlış tarafa çekerse özgün sorgu hâlâ oradadır.
"""
import re

# (gündelik kalıp, eklenecek kanun terimleri)
# Kalıplar dar tutulur: yanlış eşleşme sorguyu alakasız bir alana çeker.
SOZLUK = [
    # --- kira ---
    (re.compile(r"\bev sahib|\bmülk sahib|\bkiraya veren", re.I),
     ["kiraya veren"]),
    (re.compile(r"\btahliye|\bevden çıkar|\bkiracıyı çıkar|\bboşalt", re.I),
     ["boşaltma", "sözleşmenin sona ermesi"]),
    (re.compile(r"\bkira(yı|ya|sı)? (ne kadar )?(artır|zam|yüksel)|kira artış|kira zam", re.I),
     ["kira bedelinin belirlenmesi", "tüketici fiyat endeksi", "değişim oranı"]),
    (re.compile(r"\bihtiyac[ıi]m var\b|\bkendi ihtiyac|\bgereksinim", re.I),
     ["gereksinimi", "kiraya veren"]),
    (re.compile(r"\bdepozito|\bteminat", re.I),
     ["kiracının güvence vermesi"]),

    # --- tüketici ---
    (re.compile(r"\bbozuk\b|\bayıplı|\bkusurlu\b|\barızalı|\bçalışmıyor\b", re.I),
     ["ayıplı mal", "tüketicinin seçimlik hakları"]),
    (re.compile(r"\biade\b|\bgeri (ver|gönder|iade)|\bvazgeç", re.I),
     ["cayma hakkı", "sözleşmeden dönme"]),
    (re.compile(r"\binternetten (al|sipariş)|\bonline (al|sipariş)|\bmesafeli", re.I),
     ["mesafeli sözleşmeler"]),
    (re.compile(r"\bgaranti\b", re.I), ["garanti belgesi"]),
    (re.compile(r"\bhakem heyeti|\btüketici mahkemesi|\bşikayet ed", re.I),
     ["tüketici hakem heyeti"]),

    # --- iş ---
    (re.compile(r"\bişten (çıkar|at|kov)|\bkovul|\bfesh", re.I),
     ["iş sözleşmesinin feshi", "süreli fesih"]),
    (re.compile(r"\bkıdem|\bihbar tazminat", re.I), ["kıdem tazminatı"]),
    (re.compile(r"\byıllık izin|\bizin hakk|\btatil hakk", re.I),
     ["yıllık ücretli izin"]),
    (re.compile(r"\bfazla mesai|\bfazla çalış", re.I), ["fazla çalışma"]),

    # --- aile ---
    (re.compile(r"\bboşan", re.I), ["boşanma", "evlilik birliği"]),
    (re.compile(r"\bnafaka", re.I), ["yoksulluk nafakası"]),
    (re.compile(r"\bvelayet|\bçocuğun (velayeti|bakımı)", re.I),
     ["kişisel ilişki kurulması"]),

    # --- trafik ---
    (re.compile(r"\bkaza (yaptım|geçir)|\btrafik kazas|\btutanak", re.I),
     ["trafik kazası", "kaza tespit tutanağı"]),
    (re.compile(r"\btrafik sigortas|\bzorunlu sigorta", re.I),
     ["mali sorumluluk sigortası"]),

    # --- kişisel veri ---
    (re.compile(r"\bverilerim|\bkişisel veri", re.I), ["kişisel veri", "veri sorumlusu"]),
    (re.compile(r"\bsil(inme|dir)|\bunutulma hakk", re.I),
     ["kişisel verilerin silinmesi"]),

    # --- usul ---
    (re.compile(r"\barabulucu", re.I), ["arabuluculuk", "dava şartı"]),
    (re.compile(r"\bzamanaşım|\bsüre(si)? geçt|\bne kadar süre içinde dava", re.I),
     ["zamanaşımı"]),
]


def genislet(soru):
    """Soruya, içinde geçmeyen kanun terimlerini ekler. Özgün metin korunur."""
    metin = soru or ""
    dusuk = metin.lower()
    ekler = []
    for desen, kanun_terimleri in SOZLUK:
        if not desen.search(metin):
            continue
        for terim in kanun_terimleri:
            if terim.lower() not in dusuk and terim not in ekler:
                ekler.append(terim)
    return f"{metin} {' '.join(ekler)}" if ekler else metin
