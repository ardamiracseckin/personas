# personas — mevzuat asistanı

Türk mevzuatı üzerinde çalışan, tamamen çevrimdışı bir **madde bulucu**. Hukuki bir durumu
gündelik dille anlatırsınız; asistan ilgili kanun maddelerini bulur, alaka sırasıyla dizer ve
maddenin tam metnini gösterir. Cevap üretmez — ekranda gördüğünüz her kelime kanun metnindendir.

> Bu bir madde bulucudur, hukuki tavsiye değildir. Avukatın yerine geçmez; avukata gitmeden önce
> hangi kuralın işlediğini bilmenizi sağlar.

## Neden cevap üretmiyor

Ölçüm gösterdi ki bu boyuttaki yerel modeller Türkçe hukuk metninde yanlış cümleler kuruyor —
"arabulucuya gitmek zorunlu değildir" gibi. Hukukta uydurulmuş bir cümle, cevapsızlıktan beterdir:
kaynak gösterildiği için doğrulanmış izlenimi verir.

Bu yüzden yanıt tamamen çıkarımsaldır. Maddenin tam metni gösterilir ve soruyla en çok örtüşen
cümle içinde işaretlenir. Kullanıcı 3.055 parçalık yığından beş maddeye, oradan da bir cümleye
iner; kazanç budur.

Aynı sebeple **tahmin ve tavsiye isteyen sorulara madde gösterilmez.** "Bu davayı kazanır mıyım",
"ne yapmalıyım" gibi sorular somut olaya, delile ve mahkemenin takdirine bağlıdır; bir madde
listesi bunu cevaplamaz ama cevapladığı izlenimi yaratır.

## Bilgi tabanı

`mevzuat.gov.tr` üzerinden indirilmiş, değişiklikleri işlenmiş güncel metinler. Hiçbir madde elle
yazılmadı ya da özetlenmedi.

| Kanun | Madde |
|---|---|
| 2918 Karayolları Trafik Kanunu | 187 |
| 4721 Türk Medeni Kanunu | 1016 |
| 4857 İş Kanunu | 136 |
| 6098 Türk Borçlar Kanunu | 642 |
| 6100 Hukuk Muhakemeleri Kanunu | 455 |
| 6502 Tüketicinin Korunması Hakkında Kanun | 92 |
| 6698 Kişisel Verilerin Korunması Kanunu | 33 |
| 7036 İş Mahkemeleri Kanunu | 13 |

Toplam 2.607 madde → 3.175 parça. Parçalama birimi maddedir: uzun maddeler fıkra sınırından
bölünür, her parça kendi kanun ve madde numarasını taşır. Ek ve geçici maddeler ayrı numaralandırılır
(`GEÇİCİ MADDE 2` ile `MADDE 2` bambaşka hükümlerdir). `(Değişik:2/3/2024-7499/33 md.)` gibi
ibareler korunur — maddenin hangi tarihli hâli olduğunu yalnızca onlar söyler.

## Nasıl çalışır

```
soru
 ├─ tavsiye/tahmin istiyorsa → kapsam dışı, madde gösterilmez
 └─ değilse
     ├─ kosinüs benzerliği      anlamı yakalar          (bütün korpus)
     ├─ gövde bazlı BM25        terimi birebir yakalar  (bütün korpus)
     │   └─ 60 aday
     │       └─ bulanık eşleşme  yazım hatasını affeder (yalnız adaylarda)
     └─ eşiği geçen en iyi 5 madde
         ├─ hiçbiri geçmediyse → "yüklü kanunlarda bulamadım"
         └─ geçtiyse → en yakın madde öne, kalanlar alaka sırasıyla
```

Üç sinyal de gerekli. Yalnız kosinüs doğru maddeyi ilk sırada 2/10 buluyordu; BM25 eklenince 4/10
oldu. Türkçe eklemeli olduğu için BM25 gövde bazlıdır: sorguda "tahliye taahhüdü", kanunda
"tahliye taahhüdünde".

Erişimden önce soru, **kanun terimleriyle genişletilir** (`app/terimler.py`). Kullanıcı "tahliye"
diyor, kanun "boşaltma" diyor; kullanıcı "ev sahibi" diyor, kanun "kiraya veren" diyor. Elle
kurulmuş, korpustan doğrulanmış bir sözlük bu boşluğu kapatıyor: doğru madde ilk beşte bulunma
oranı %67'den %89'a çıktı. Sözlükteki her terimin kanun metninde birebir geçtiğini bir test her
koşumda denetler.

## Kurulum

```bash
# 1) Foundry Local (sohbet modeli yalnız eski asistan kipi için gerekir)
brew install microsoft/foundrylocal/foundrylocal

# 2) Python ortamı
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) Kanun metinlerini yükle (data/mevzuat/ altındaki PDF'ler)
python scripts/mevzuat_yukle.py --temizle
```

Yükleme 3.055 parçayı yaklaşık 100 saniyede gömer. Kanun metinleri depoda `data/mevzuat/` altında
durur; güncellemek için `mevzuat.gov.tr` üzerinden yeni PDF'i indirip aynı komutu çalıştırmak
yeterlidir.

## Kullanım

```bash
uvicorn server.main:app --port 8000     # arayüz → http://localhost:8000
python scripts/mevzuat_olcum.py         # değerlendirme koşumu
```

Arayüz dil modeli çağırmaz, tamamen çevrimdışı çalışır ve hiçbir dış kaynağa bağlanmaz.

Aynı sunucuda ikinci bir arayüz daha var: **`/sohbet`** adresinde projenin kişisel asistan kipi
duruyor — sohbet geçmişi, Apple Takvim/Mail, WhatsApp taslağı ve uygulama açma. O kip dil modelini
çağırır ve Foundry Local gerektirir. İki arayüz aynı bilgi tabanını paylaşır; şu an yüklü olan
kanun metnidir.

## Ölçüm

42 soruluk sabit set (`eval/mevzuat_sorular.json`): 27 cevaplanabilir (yedi alan), 6 hukuk dışı,
5 tavsiye isteyen, 4 uç durum. Beklenen madde numaraları korpustaki başlıklardan doğrulanmıştır;
bir test bunu her koşumda kontrol eder.

| Ölçüt | Sonuç |
|---|---|
| Doğru madde 1. sırada | 16/27 (%59) |
| Doğru madde ilk 3'te | 22/27 (%81) |
| **Doğru madde ilk 5'te** | **24/27 (%89)** |
| **Doğru kanundan aday geldi** | **27/27 (%100)** |
| Hukuk dışı soruda çekimserlik | 6/6 |
| Tavsiye isteyen soruda ret | 5/5 |
| Ortalama süre | 0,38 sn |

Ayrıntılı çözümleme, denenip elenen sekiz yaklaşım ve ölçümün kendi hataları:
[`docs/eval/mevzuat-degerlendirme.md`](docs/eval/mevzuat-degerlendirme.md).

## Sınırlar

- **Doğru madde ilk sırada %59.** Beş adayın içinde bulunma oranı %89; yine de her on sorudan
  birinde doğru madde listede hiç yoktur. Arayüz bu yüzden "cevap budur" demez.
- En zayıf alan usul (1/3). Kira ve tüketici, terim sözlüğüyle 1/4 ve 2/4'ten 2/4 ve 3/4'e çıktı.
- Yalnız sekiz kanun yüklü; dışındaki her konu kapsam dışıdır ve asistan bunu söyler.
- Metinler indirildiği tarihteki hâldir. Mevzuat değişir.

## Proje yapısı

```
app/
  mevzuat.py           kanun metnini madde bazlı parçalar
  mevzuat_yanit.py     aday maddeleri hazırlar, en yakın cümleyi çıkarır
  hukuki_kapsam.py     tavsiye/tahmin isteyen soruları yakalar
  bm25.py              gövde bazlı kelime araması
  terimler.py          gündelik dil → kanun terimi sözlüğü
  retriever.py         kosinüs + BM25 + bulanık eşleşme harmanı
  ingest.py            kanun PDF'lerini bilgi tabanına yazar
server/
  main.py              "/" mevzuat, "/sohbet" kişisel asistan
  static/mevzuat.*     mevzuat arayüzü, bağımlılıksız
  static/{index,app,styles}.*  kişisel asistan arayüzü
scripts/
  mevzuat_yukle.py     kanunları yükle
  mevzuat_olcum.py     değerlendirme koşumu
eval/mevzuat_sorular.json
docs/eval/mevzuat-degerlendirme.md
data/mevzuat/          kanun PDF'leri (mevzuat.gov.tr)
```

Bu dal (`mevzuat-uzmani`) projenin bilgi tabanını ve kimliğini değiştirir. Kişisel asistan sürümü
(teknik notlar, takvim/mail/WhatsApp araçları) `main` dalında durur.

## Testler

```bash
python -m pytest -q     # 346 test; Foundry ve model gerektirmez
```
