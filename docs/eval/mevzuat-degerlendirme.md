# Mevzuat Asistanı — Değerlendirme Raporu

*30 Ağustos 2026 · `mevzuat-uzmani` dalı*

## 1. Ne değişti

Bilgi tabanı, elle yazılmış teknik notlardan **gerçek kanun metnine** çevrildi. Sekiz kanunun
`mevzuat.gov.tr` üzerinden indirilmiş, değişiklikleri işlenmiş güncel hâli kullanılıyor:

| Kanun | Madde | Parça |
|---|---|---|
| 2918 Karayolları Trafik Kanunu | 187 | 363 |
| 4721 Türk Medeni Kanunu | 1016 | 1030 |
| 4857 İş Kanunu | 136 | 213 |
| 6098 Türk Borçlar Kanunu | 642 | 659 |
| 6100 Hukuk Muhakemeleri Kanunu | 455 | 529 |
| 6502 Tüketicinin Korunması Hakkında Kanun | 92 | 182 |
| 6698 Kişisel Verilerin Korunması Kanunu | 33 | 71 |
| 7036 İş Mahkemeleri Kanunu | 13 | 22 |
| **Toplam** | **2.607** | **3.175** |

Hiçbir madde elle yazılmadı, özetlenmedi ya da yeniden ifade edilmedi. Metnin güncelliği
doğrulandı: KVKK'nın 6. maddesi `(Mülga:2/3/2024-7499/33 md.)` ve `(Değişik:2/3/2024-7499/33 md.)`
ibarelerini taşıyor — yani 2024 değişikliği işlenmiş hâl. Kanunun ilk kabul edildiği metin
(Resmî Gazete baskısı) bu ibareleri taşımaz ve kullanılsaydı asistan yürürlükten kalkmış hüküm
gösterirdi.

Bu, önceki korpusun 53 katı. Sıçramanın sebebi ölçüm gereksinimiydi: önceki değerlendirme
raporunda "58 parçalık bir bilgi tabanında %100 skorlar, erişimin ölçekte çalıştığını kanıtlamaz"
diye yazılmıştı. Bu rapor o uyarının haklı çıktığını belgeliyor.

## 2. Parçalama: madde birimi

Kanun metni genel parçalayıcıya verilemez; karakter sınırıyla bölmek maddeyi ortasından keser ve
atıf anlamını yitirir. `app/mevzuat.py` madde birimiyle çalışır:

- İki resmî yazım biçimi tanınır: `Madde 12 –` (2011 öncesi) ve `MADDE 12- (1)` (2011 sonrası).
- Ek ve geçici maddeler ayrı numaralandırılır. `GEÇİCİ MADDE 2` ile `MADDE 2` bambaşka
  hükümlerdir; karıştırılmaları yanlış hükme göndermek demektir.
- Değişiklik ibareleri korunur. Maddenin hangi tarihli hâli olduğunu yalnızca onlar söyler.
- Uzun maddeler fıkra sınırından bölünür; her parça aynı maddeye atıf yapar.
- Atıf parçanın ilk satırına yazılır, böylece modele giden bağlamda madde numarası hep bulunur.

## 3. Yöntem

42 soruluk sabit set (`eval/mevzuat_sorular.json`), dört kategori:

| Kategori | Adet | Beklenen davranış |
|---|---|---|
| Cevaplanabilir | 27 | Doğru maddeyi aday listesinde göster |
| Hukuk dışı | 6 | İlgili madde yok de |
| Tavsiye isteyen | 5 | Kapsam dışı diye reddet |
| Uç durum | 4 | Çökme yok |

Cevaplanabilir soruların beklenen madde numaraları **korpustaki başlıklardan doğrulandı**,
ezberden yazılmadı. Bir test bunu her koşumda kontrol ediyor: beklenen 27 maddenin hepsi bilgi
tabanında gerçekten var mı (`tests/test_mevzuat_soru_seti.py`).

Ölçüm dil modeli çağırmaz. Asistan cevap üretmiyor, madde çıkarıyor; ölçülen şey erişimin doğru
maddeyi bulup bulmadığıdır.

## 4. Sonuçlar

| Ölçüt | Sonuç |
|---|---|
| Doğru madde 1. sırada | 16/27 (%59) |
| Doğru madde ilk 3'te | 22/27 (%81) |
| Doğru madde ilk 5'te | 24/27 (%89) |
| **Doğru kanundan aday geldi** | **27/27 (%100)** |
| Hukuk dışı soruda çekimserlik | 6/6 |
| Tavsiye isteyen soruda ret | 5/5 |
| Uç durumda çökme | 0/4 |
| Ortalama süre | 0,38 sn |
| p95 süre | 0,51 sn |

Alan bazında doğru madde ilk sırada: iş 3/4, trafik 3/4, tüketici 3/4, aile 2/4, KVKK 2/4,
kira 2/4, usul 1/3.

**En anlamlı sayı %93.** Asistan neredeyse her zaman doğru kanuna gidiyor; zorlandığı yer doğru
kanunun içinde doğru maddeyi seçmek. Kullanıcı açısından bu, 3.055 parçalık yığından beş maddeye
inmenin çalıştığı anlamına gelir — vaat buydu.

Başarısızlıklar çoğunlukla komşu madde: "Bir yıldır çalışan işçinin kaç gün izni olur" sorusunda
İş Kanunu md. 53 yerine md. 54 geliyor (ikisi de yıllık izin hükmü). Kira ve tüketici alanlarında
ise gerçek sapmalar var: kira artışı sorusuna Türk Borçlar Kanunu'nun ev düzeni içinde çalışmaya
ilişkin md. 418'i geliyor.

## 5. Denenip elenen yaklaşımlar

Erişimi iyileştirmek için sekiz yol denendi ve hepsi aynı on soruluk çekirdek üzerinde ölçüldü.
Tablo, neyin işe yaramadığını da gösteriyor — projenin en öğretici kısmı burası.

| Yaklaşım | hit@1 | hit@3 |
|---|---|---|
| Yalnız kosinüs (başlangıç) | 2/10 | 5/10 |
| Doğru kanunla sınırlama (kâhin yönlendirme) | 3/10 | 6/10 |
| Korpusu ilgili bölümlere daraltma (3.069 → 1.027) | 2/10 | 6/10 |
| Madde başlığıyla eşleştirme | 0/10 | 0/10 |
| BM25, tam kelime | 1/10 | 3/10 |
| **BM25 gövde + kosinüs harmanı** | **4/10** | 5/10 |
| Sıra birleştirme (RRF) | 4/10 | 5/10 |
| Model ile sorgu yeniden yazma | 0–1/10 | 1–3/10 |
| Model ile yeniden sıralama | 2/10 | — |
| *Elle kanun diliyle sorma (tavan)* | *5/10* | *7/10* |

**Sorun ölçek değil, dil.** Kullanıcı "Ev sahibi kirayı ne kadar artırabilir?" diye soruyor; kanun
"kira bedelinin belirlenmesinde tüketici fiyat endeksindeki oniki aylık ortalamalara göre değişim
oranı" diyor. Aynı soru kanun diliyle sorulduğunda isabet ikiye katlanıyor. Ama bu çeviriyi
yapacak model yok: `qwen3.5-2b-text` soruyu terimlere çevirmek yerine cevaplamaya kalkıp yanlış
cevaplar üretti ("arabulucuya gitmek zorunlu değildir" — yanlış), `phi-4-mini` ise anlamsız
kelimeler yazdı ("İstiyarlık", "restitüsyon hakı"). Yeniden sıralamada da model içeriğe bakmadan
listenin sonunu seçti.

**Embedding modeli de kaldıraç değil.** `multilingual-e5-large` (2,2 GB) 8 GB'lık makinede belleğe
sığmadı, diskten sayfalayarak 15 dakika CPU harcayıp tek parça gömemedi. `mpnet-base` (1 GB) aynı
havuzda ölçüldüğünde on soruda **bir tane** kazandırdı (hit@1 6/10 karşı 5/10); karşılığında beş
kat büyük model, 25 dakikalık gömme ve daha yavaş sorgu. Alınmadı.

Türkçenin eklemeli yapısı BM25'i tek başına işe yaramaz kılıyor: sorguda "tahliye taahhüdü",
kanunda "tahliye taahhüdünde". Kelimeler ilk beş karaktere indirilerek eşleştirilince tam kelime
eşleşmesinin 1/10'u 4/10'a çıktı.

## 5b. Kira ve tüketici alanlarının düzeltilmesi

İlk ölçümde kira 1/4, tüketici 2/4 ile en zayıf alanlardı. Dört ayrı sebep denendi ve üçü elendi:

| Denenen | Sonuç |
|---|---|
| PDF çıkarımını `layout` kipine almak | Kırık kelime 533 → 59 (%89), 20 madde daha bulundu; **isabet değişmedi** |
| Başlık hiyerarşisini künyeye taşımak (bütün yığın) | hit@1 15/27 → 14/27, doğru kanun 25/27 |
| Yalnız en yakın üst başlığı taşımak | hit@1 14/27, değişiklik yok |
| **Gündelik dil → kanun terimi sözlüğü** | **ilk 5'te 18/27 → 24/27** |

Hiyerarşi neden zarar verdi: "İKİNCİ AYIRIM Konut ve Çatılı İşyeri Kiraları" satırı o bölümdeki
yüzlerce maddenin hepsinde aynıdır. Ayırt etmez, tersine benzeştirir. Künyeye eklenince doğru
kanundan aday getirme oranı bile 27/27'den 25/27'ye düştü. Kod ve testleri kaldırıldı; kalan tek
iz bu satırdır.

Asıl sebep KR02'de çıplak görünüyordu: kullanıcı "tahliye taahhüdü" diyor, kanun bu kelimeyi hiç
kullanmıyor — "kiralananı belli bir tarihte boşaltmayı üstlendiği hâlde boşaltmamışsa" diyor.
Kullanıcının kelimesi uygulamadan, kanunun kelimesi metinden geliyor. Parçalama bunu düzeltemez.

`app/terimler.py` bu boşluğu elle kurulmuş dar bir sözlükle kapatıyor: "tahliye" → "boşaltma",
"ev sahibi" → "kiraya veren", "bozuk ürün" → "ayıplı mal". İki kural var. Birincisi, hiçbir terim
uydurulmaz: sözlükteki her ifadenin kanun metninde birebir geçtiğini bir test her koşumda
doğrular. İkincisi, terim madde başlığına değil sözcük dağarcığına eşlenir — ilk sürümde
"verilerim" → "ilgili kişinin hakları" yazıyordu, o KVKK md. 11'in başlığıdır ve bütün KVKK
sorularını o maddeye çekiyordu; "nasıl başvururum" sorusunun cevabı ise md. 13'tür. Genel terime
("kişisel veri", "veri sorumlusu") çevrilince KVKK 1/4'ten 2/4'e döndü.

Aynı çeviriyi modele yaptırmak daha önce denenmiş ve ölçümde batmıştı (Bölüm 5). Model bilgi
üretmekte kötü, ama insan eliyle yazılmış yirmi küçük kural işi görüyor.

## 6. Ölçümün kendi hataları

Bu projede iki kez ölçüm, ölçtüğü şeyi bozdu:

**Kelime katmanı yanlış yerde çalışıyordu.** Sözlüksel eşleşme yalnız kosinüsün getirdiği 60
adayda koşuyordu; kosinüs doğru maddeyi kaçırdığında kelime katmanı onu hiç göremiyordu. Kanunda
ayırt edici terim birebir geçtiği için bu katmanın bütün korpusu görmesi gerekiyordu. Ayrıca
`SequenceMatcher` tabanlı bulanık eşleşme 3.069 parçada sorgu başına 8,7 saniye sürüyordu; iki
katman ayrılınca erişim 6,53 saniyeden 0,43 saniyeye indi.

**BM25 normalizasyonu çekimserliği kırdı.** Puanlar sorgu içi maksimuma bölününce alakasız bir
soruda bile en iyi parça 1,0 alıyordu ve "bilmiyorum" diyebilme özelliği kayboldu. Ham puanlar
ölçüldüğünde ayrım göründü — konuyla ilgili sorularda 10–19, alakasızlarda 7–9,6 — ve sabit bir
doyum değerine bölmek mutlak büyüklüğü korudu.

Eşikler de yeniden ölçüldü: `DENSE_FLOOR` 0,10'dan 0,30'a, `SIM_THRESHOLD` 0,34'ten 0,38'e çıktı.
Eski tabanla "Bugün hava nasıl olacak?" sorusu kanun metnine bağlanıyordu, çünkü "nasıl" ve
"olacak" gibi yaygın kelimeler uzun maddelerde bulunuyor: bulanık skor 0,75'e çıkarken kosinüs
0,14'te kalıyordu. Düzeltme sonrası hukuk dışı sorularda çekimserlik 2/6'dan 6/6'ya çıktı ve
erişim isabetinden kayıp olmadı.

## 7. Tasarım kararları

**Asistan cevap üretmez, madde çıkarır.** Ölçüm gösterdi ki bu boyuttaki yerel modeller Türkçe
hukuk metninde yanlış cümleler kuruyor. Hukukta uydurulmuş bir cümle cevapsızlıktan beterdir:
kaynak gösterildiği için doğrulanmış izlenimi verir. Bu yüzden ekranda görünen her kelime kanun
metnindendir; maddenin tam metni gösterilir ve soruyla en çok örtüşen cümle içinde işaretlenir.

**Tavsiye isteyen sorulara madde gösterilmez.** "Bu davayı kazanır mıyım", "ne yapmalıyım" gibi
sorular somut olaya, delile ve mahkemenin takdirine bağlıdır; bir madde listesi bunu cevaplamaz
ama cevapladığı izlenimi yaratır. Kural yokken beş tahmin sorusunun dördüne madde listesi
çıkıyordu; şimdi 5/5 reddediliyor. Dedektör dar tutuldu: ilk hâli "Verilerimin silinmesini
isteyebilir miyim?" sorusunu da reddediyordu, oysa o meşru bir bilgi sorusudur ve KVKK md. 7
cevaplıyor.

**Arayüz vaadi ölçümle uyumlu.** Doğru madde ilk sırada %56 bulunduğu için ekran "cevap budur"
demiyor; "en yakın madde bu, karar senin, maddenin tamamını okumadan sonuç çıkarma" diyor ve altta
"bu bir madde bulucudur, hukuki tavsiye değildir" yazıyor.

## 8. Sınırlar

- **Doğru madde ilk sırada %59.** Beş adayın içinde bulunma oranı %89; yine de her on sorudan
  birinde doğru madde listede hiç yok.
- **En zayıf alan usul** (1/3). Kira ve tüketici terim sözlüğüyle düzeldi ama usul soruları
  ("dava dilekçesinde neler bulunur") hâlâ komşu maddelere gidiyor.
- **Terim sözlüğü elle bakım ister.** Yeni bir alan eklenirse o alanın gündelik terimleri de
  eklenmeli; sözlük kendini güncellemiyor.
- Belge sonlarındaki değişiklik tabloları ve "kanuna işlenemeyen hükümler" bölümleri de
  parçalanıyor. Kesme işaretleri güvenilir olmadığı için (bazıları gerçek madde başlığı)
  ayıklanmadı; ölçümde belirgin zarar görülmedi.
- Yalnız sekiz kanun yüklü. Bu kanunların dışındaki her konu kapsam dışıdır ve asistan bunu
  söyler — ama kullanıcı hangi kanunların yüklü olduğunu bilmezse neyi soramayacağını da bilmez;
  arayüz bu yüzden yüklü kanunları açılışta listeler.
- Metinler indirildiği tarihteki hâldir. Mevzuat değişir; güncel tutmak yeniden indirmeyi
  gerektirir.
