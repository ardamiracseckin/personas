# personas — Değerlendirme Raporu (Faz 3)

**Tarih:** 19.08.2026 · **Donanım:** Apple M2, 8 GB RAM, macOS 26.5.1
**Sohbet modeli çalışma zamanı:** Microsoft Foundry Local · **Embedding:** fastembed (yerel)

Bu rapor, asistanın Microsoft staj planındaki 5. hafta ("System Testing & Evaluation")
beklentilerini karşılamak için yapılan ölçümleri, ölçümlere dayanarak alınan kararları ve kalan
zayıflıkları belgeler. Tüm koşumlar `scripts/evaluate.py` ile üretilmiştir ve
`docs/eval/sonuclar-*.md` dosyalarında ham hâlleriyle durur.

---

## 1. Yöntem

### 1.1 Soru seti

`eval/questions.json` — 44 soru, beş kategori:

| Kategori | Adet | Beklenen davranış |
|---|---|---|
| `cevaplanabilir` | 14 | Belgelerden doğru cevap + doğru kaynak |
| `yazim_hatasi` | 14 | Aynı soruların bozuk yazımlı hâli; yine doğru kaynağa gitmeli |
| `cevaplanamaz` | 6 | "Bilgim yok" demeli, uydurmamalı |
| `uc_durum` | 4 | Boş sorgu, tek kelime, çok genel, çok uzun soru — çökmemeli |
| `yonlendirme` | 6 | Takvim / mail / uygulama / belge aracına doğru gitmeli |

Cevaplanabilir soruların her birinde beklenen kaynak dosya adı yazılıdır; bu sayede erişim başarısı
dil modeli hiç çalıştırılmadan ölçülebilir.

### 1.2 Ölçülen metrikler

- **Yönlendirme doğruluğu** — `router.route()` beklenen aracı ve niyeti seçti mi. Deterministik.
- **Erişim isabeti (hit@K)** — beklenen kaynak, eşiği geçen ilk K parça arasında mı. Deterministik.
- **Çekimserlik** — cevaplanamaz sorularda asistan bilmediğini söyledi mi. İki katmanda oluşur:
  benzerlik eşiği hiç parça bırakmazsa *erişim* katmanı, parça geldiği hâlde model bağlamı yetersiz
  bulursa *model* katmanı çekimser kalır.
- **Gecikme** — soru başına uçtan uca süre (ortalama, p50, p95). Program hedefi ~1–3 saniye.
- **Kalite** — cevaplanabilir sorularda 0–2 puan. İlk ölçümlerde elle yapıldı; sonrasında
  `eval/questions.json` içindeki `expected_substrings` alanıyla **otomatik** hâle getirildi
  (beklenen ifadelerin hepsi geçerse 2, bir kısmı geçerse 1, hiçbiri geçmezse 0; boşluklar
  yok sayılır). Böylece model değiştirmek insan puanlaması gerektirmiyor. İki yöntem aynı
  sıralamayı verdi (Bölüm 5).

- **Sadakat** — cevaptaki içerik kelimelerinin kaçı getirilen parçalarda geçiyor (0–1). Kalite
  puanından farklıdır: o "doğru bilgi cevapta var mı" der, sadakat "bilgi bağlamdan mı geliyor"
  der. Model doğru cevabı ezberinden de verebilir; o durumda RAG zinciri çalışmamıştır. Sorudan
  gelen kelimeler ve modelin kendi cümle kurma kelimeleri sayılmaz. Çekimser cevaplarda ölçülmez.
- **Kod sadakati** — cevapta ters tırnak içinde geçen her komut bağlamda birebir var mı. İkili bir
  ölçüt: sözlüksel oran bulanıktır ama komut uydurmak, kullanıcının çalıştıracağı yanlış komut
  demektir.

Ölçümden önce her koşumda bir **ısınma turu** yapılır; ilk çağrıda model belleğe yüklendiği ve
embedding modeli ilk kez başlatıldığı için bu süre ölçüme karışmamalıdır.

---

## 2. Bilgi tabanı ve parçalama

Faz 3 başlangıcında bilgi tabanı 3 belge ve **toplam 3 parça**dan ibaretti; belgeler
`MAX_CHUNK_CHARS` sınırının çok altında kaldığı için parçalama hiç devreye girmiyor, erişim fiilen
"üç belgeden birini seç"e indirgeniyordu. Microsoft planının istediği 5–10 belge / 1–3 paragraflık
parça yapısına ulaşmak için belge seti 8 nota çıkarıldı.

Ayrıca `chunk_text()` başlık farkındalıklı hâle getirildi: markdown başlıkları parça sınırı sayılıyor
ve her parça kendi başlığını taşıyor. Böylece parça, tek başına hangi konuya ait olduğunu belirtiyor.

| Ayar | Parça sayısı | Ortalama uzunluk | Medyan |
|---|---|---|---|
| `max_chars=400` | 88 | 292 | 312 |
| `max_chars=500` | 74 | 344 | 358 |
| `max_chars=600` | 63 | 401 | 396 |
| **`max_chars=800` (seçilen)** | **58** | **433** | **398** |
| `max_chars=1000` | 58 | 433 | 398 |

800 ile 1000 aynı sonucu veriyor: parçaları bölen şey karakter sınırı değil, başlık sınırları. Yani
parçalar belgelerin kendi bölüm yapısına oturuyor ve ortalama 433 karakter (~1–3 paragraf) ile
planın istediği aralıkta kalıyor. Sonuç: **8 belge, 58 parça.**

---

## 3. Erişim eşiği taraması

> Bu bölüm **yalnız kosinüs** skoruyla yapılan ilk taramayı belgeler. Erişim katmanı sonradan
> hibrit hâle geldi; güncel tarama ve seçilen eşik (0.34) Bölüm 9'dadır.

İlk ayarlar (`SIM_THRESHOLD = 0.20`, `TOP_K = 3`) ölçüme değil tahmine dayanıyordu. Tarama
(`python scripts/evaluate.py --esik 0.15,…,0.50 --k 2,3,5`) şunu gösterdi:

| Eşik | Erişim isabeti | Çekimserlik | Denge |
|---|---|---|---|
| 0.15 | 100% | 0% | 50% |
| **0.20 (eski)** | **100%** | **0%** | **50%** |
| 0.25 | 100% | 33% | 67% |
| 0.30 | 100% | 33% | 67% |
| 0.35 | 100% | 50% | 75% |
| **0.40 (yeni)** | **100%** | **83%** | **92%** |
| 0.45 | 86% | 100% | 93% |
| 0.50 | 57% | 100% | 79% |

*(K = 2, 3 ve 5 için isabet oranları aynı çıktı; K erişim başarısını değil yalnızca bağlam
uzunluğunu etkiliyor.)*

**En kritik bulgu:** eski eşik 0.20'de cevaplanamaz soruların **altısı da** eşiği geçiyordu. Yani
"Docker imajı nasıl oluşturulur?" sorusunda modele alakasız macOS notları bağlam olarak gidiyor,
asistanın uydurma cevap üretmesi tamamen modelin insafına kalıyordu.

Skorların dağılımı şöyle:

- Cevaplanabilir soruların **en düşük** skoru: **0.430** (C03 — "Yarım kalan değişiklikleri geçici
  olarak nasıl saklarım?")
- Cevaplanamaz soruların **en yüksek** skoru: **0.440** (B06 — "Fotoğrafta diyafram değeri neyi
  etkiler?", macOS notlarındaki "ekran görüntüsü / kamera" bağlamına yakın düşüyor)

İki dağılım 0.43–0.44 aralığında çakıştığı için **kusursuz ayıran bir eşik yok**. Seçim
`SIM_THRESHOLD = 0.40` oldu: erişim isabetini tam tutar (14/14), çekimserliği 0/6'dan 5/6'ya
çıkarır, kalan tek sızıntıyı da istemdeki "bağlamda yoksa bilmiyorum de" kuralına bırakır.
Bu ikinci katmanın ne kadar güvenilir olduğu modele göre değişiyor (bkz. Bölüm 5 ve 7):
qwen2.5-1.5b sızan soruda çekimser kalırken, seçilen phi-4-mini kendi genel bilgisinden cevap verdi.

`TOP_K` 3'te bırakıldı: K=1 iken isabet 13/14'e düşüyor (C14 "VS Code'da projenin tamamında nasıl
arama yaparım?" sorusunda ilk sıraya `python-notlari.md` geliyor, doğru kaynak ikinci sırada),
K=2 ve üzeri 14/14 veriyor. K=3 marj bırakırken bağlamı gereksiz büyütmüyor.

---

## 4. Deterministik sonuçlar

| Metrik | Sonuç |
|---|---|
| Yönlendirme doğruluğu | **6/6 (%100)** |
| Erişim isabeti hit@3 (eşik 0.40) | **14/14 (%100)** |
| Erişim isabeti hit@1 | 13/14 (%93) |
| Erişim katmanında çekimserlik | 5/6 (%83) |

*(Yönlendirme seti, Bölüm 8'de anlatılan hatalar bulunduktan sonra çakışan örneklerle
genişletildi; 6/6 sonucu düzeltme sonrası ölçümdür.)*

Bu metrikler dil modeli çalıştırılmadan ölçüldüğü için saniyeler sürer ve
`tests/test_eval_questions.py` içinde regresyon testi olarak da koşar: soru setindeki her
yönlendirme sorusu ve her cevaplanabilir sorunun beklenen kaynağı, testler her çalıştığında
yeniden doğrulanır.

---

## 5. Model karşılaştırması

Aynı soru seti, 8 GB belleğe sığan dört sohbet modeliyle koşuldu. Her koşumdan önce bir önceki
model `foundry model unload` ile bellekten boşaltıldı ve ısınma turu yapıldı.

Kalite iki yöntemle ölçüldü: **elle** (2 = doğru ve yeterli, 1 = kısmen doğru, 0 = yanlış) ve
**otomatik** (beklenen ifadelerin hepsi geçerse 2, bir kısmı geçerse 1, hiçbiri geçmezse 0).

| Model | Boyut | Oto kalite | Elle kalite | p50 | p95 | Çekimserlik | Sonuç |
|---|---|---|---|---|---|---|---|
| **phi-4-mini** | 3,7 GB | **24/28 (%86)** | **22/28 (%79)** | 4,72 sn | 12,58 sn | 5/6 | **Seçilen** |
| qwen2.5-1.5b | 1,5 GB | 20/28 (%71) | 18/28 (%64) | **2,98 sn** | **5,88 sn** | **6/6** | Hafif alternatif |
| phi-3.5-mini | 2,2 GB | 14/28 (%50) | 11/28 (%39) | 4,47 sn | 12,91 sn | 5/6 | Elendi |
| qwen3-1.7b | 1,4 GB | 20/28 (%71)* | — | 8,36 sn | 10,04 sn | 5/6 | Elendi (biçim) |

*\* Aldatıcı bir puan; nedeni 5.5'te.*

Gecikmeler koşumdan koşuma değişiyor (phi-4-mini iki ayrı koşumda p50 3,95 ve 4,72 saniye verdi).
Modeller arası fark bu oynaklıktan büyük olduğu için sıralama etkilenmiyor, ancak tek bir ondalık
basamağa anlam yüklenmemeli.

### 5.1 phi-4-mini — seçilen

Cevap doğruluğunda açık ara önde. Kritik örnek: *"Git'te son commit'i geri alıp değişiklikleri nasıl
korurum?"* sorusuna doğru komutu (`git reset --soft HEAD~1`) veren tek küçük model. SQLite, RAG ve
VS Code sorularının tamamını doğru yanıtladı.

Bedeli gecikme ve bellektir: p50 ~4,7 saniye ile programın 1–3 saniyelik hedefinin dışında kalıyor
ve 8 GB belleğin yaklaşık yarısını kullanıyor. İki kalite kaybı: "stash" sorusuna commit geri alma
cevabı vermesi ve eşik sorusunda bulanık bir açıklama üretmesi.

### 5.2 qwen2.5-1.5b — hafif alternatif

Hız ve çekimserlikte üstün: hedef aralığa en yakın model ve cevaplanamaz soruların altısında da
bağlam dışına çıkmadı. Ancak iki ağır hatası var:

- **C07** — cevap üretmek yerine kendisine verilen istemi olduğu gibi geri yazdı
  (`BAĞLAM: [python-notlari.md] SORU: …`). Talimat takibinin tamamen çöktüğü tek vaka.
- **C14** — VS Code araması sorusunda belgelerde hiç geçmeyen bir PowerShell akışı uydurdu.

Sınırlı bellekli makineler için README'de alternatif olarak belgelendi.

### 5.3 phi-3.5-mini — elendi

Program planında örnek model olarak anılmasına rağmen açık farkla en zayıf sonucu verdi:

- *"Son commit'i geri al ama değişiklikleri koru"* → **`git reset --hard HEAD~1`** önerdi; bu komut
  tam olarak korunması istenen değişiklikleri siler.
- *"Klasördeki gizli dosyaları listeleyen komut"* → `Cmd + Shift + N` (yeni klasör kısayolu).
- *"SQLite'ta tablo zaten varsa…"* → `CREATE TABLE IF EXISTS` (eksik `NOT`).
- *"Fotoğrafta diyafram değeri neyi etkiler?"* → *"Cmd + Shift + 5 tuşları etkiler…"* — alakasız
  macOS parçasını bağlam sanıp cevap uydurdu. RAG'in engellemesi gereken hatanın ders kitabı örneği.

### 5.4 qwen3-1.7b — biçim nedeniyle elendi

Model düşünme (*thinking*) kipinde çalışıyor ve Türkçe cevabın önüne İngilizce muhakeme metni
yazıyor: *"Okay, the user is asking about…"*. Çoğu soruda muhakeme belirteç sınırını doldurduğu için
cevabın kendisi hiç görünmüyor. İstemin sonuna `/no_think` eklendiğinde Türkçe cevap üretiyor, ancak
tek soru 7,1 saniye sürüyor. Bu donanımda kullanılabilir değil.

### 5.5 Otomatik puanın kör noktası

qwen3-1.7b otomatik puanlamada 20/28 aldı — qwen2.5-1.5b ile aynı. Oysa cevapları kullanıcıya
gösterilemez durumda. Neden: puanlama beklenen ifadenin cevapta **geçip geçmediğine** bakıyor,
qwen3'ün sayfalarca süren İngilizce muhakemesi ise doğru komutu ("`git reset --soft HEAD~1`") zaten
içeriyor.

Yani otomatik puan **doğru bilginin bulunup bulunmadığını** ölçer, **cevabın kullanılabilir olup
olmadığını** değil. Aynı nedenle bozuk Türkçeyi veya cevaba eklenen yanlış bilgiyi de cezalandırmaz;
bu yüzden elle puandan sistematik olarak yüksektir (24/22, 20/18, 14/11).

Pratikte iki yöntem de aynı sıralamayı verdi. Doğru kullanım şudur: model denemelerini otomatik
puanla ucuza eleyip, finale kalan modelin cevaplarına bir kez gözle bakmak.

---

## 6. Seçilen yapılandırmayla ara sonuçlar

> Bu tablo, hibrit erişim ve arayüz değişikliği öncesindeki durumu belgeler.
> **Nihai sayılar Bölüm 11'dedir.**

| Metrik | Sonuç |
|---|---|
| Sohbet modeli | `phi-4-mini` (Foundry Local) |
| Yönlendirme doğruluğu | 6/6 (%100) |
| Erişim isabeti hit@3 | 14/14 (%100) |
| Otomatik kalite puanı | 24/28 (%86) |
| Cevaplanamazda çekimserlik | 5/6 |
| Ortalama / p50 / p95 süre | 4,25 sn / 4,72 sn / 12,58 sn |
| Uç durumlarda çökme | 0 |
| Test paketi | 108 test, tamamı geçiyor |

Uç durumların hiçbiri sistemi çökertmedi: boş sorgu, tek kelimelik sorgu ve çok genel soru erişim
eşiğine takılıp 0,01–0,08 saniyede "bilgi yok" cevabı aldı; çok uzun ve çok konulu soru normal
biçimde yanıtlandı.

---

## 7. Kalan zayıflıklar

1. **Bağlam dışına çıkma (phi-4-mini).** B06'da model, bağlamdaki alakasız macOS parçasını
   kullanmadı ama istemdeki "yalnızca bağlamı kullan" kuralını da çiğneyerek kendi genel
   bilgisinden doğru bir fotoğrafçılık cevabı verdi. Aynı soruda qwen2.5-1.5b çekimser kalmıştı.
   Daha güçlü model, bağlam dışına çıkma eğilimini de beraberinde getiriyor. Kullanıcı bunu ayırt
   edebilir çünkü bu tür cevaplarda kaynak gösterilmiyor.
2. **Eşik yükseltmesinin bedeli.** Eşik 0,40'a çıkarıldığında tek kelimelik "git" sorgusu da eşiğin
   altında kalıyor ve asistan bilgi yok diyor. Kısa sorgularda erişim, önceki ayara göre daha
   isteksiz.
3. **Otomatik puanın kör noktası.** Puanlama, doğru bilginin cevapta geçip geçmediğine bakar;
   cevabın okunabilir olup olmadığına bakmaz (bkz. 5.5). Finale kalan modelin cevapları bir kez
   gözle okunmalı.
4. **Soru seti tek yazarlı.** Sorular belgeleri yazan kişi tarafından hazırlandı; gerçek
   kullanıcıların soru biçimlerini temsil etmeyebilir. Program planının önerdiği "takımlar arası
   soru değişimi" uygulanmadı.
5. **Yönlendirme seti hâlâ dar.** Bölüm 8'deki hatalardan sonra çakışan örneklerle genişletildi ve
   birim testlerine bağlandı, ama toplam örnek sayısı iki haneli değil. Kapsamlı bir yönlendirme
   ölçümü için daha geniş ve başkası tarafından yazılmış bir set gerekir.
6. **Çok turlu konuşma dar kapsamlı.** Takip sorusu genişletmesi işaret zamirlerine bakar; zamir
   kullanmayan takip soruları ("aynı komutu Windows'ta nasıl yazarım?") genişletilmez.

---

## 8. Değerlendirme sonrası bulunan ve düzeltilen hatalar

Ölçümler bittikten sonra yapılan kod incelemesi, soru setinin yakalayamadığı üç hata ortaya
çıkardı. Üçü de sessizdi: hiçbiri hata vermiyor, yalnızca yanlış davranıyordu.

**8.1 Yönlendirmede araç önceliği.** Takvim kelimeleri mail kelimelerinden önce kontrol
edildiği için *"ali@example.com adresine toplantı hakkında mail gönder"* takvime gidiyordu.
*"Ahmet'e yarınki sunum için mail at"* ise çift hata veriyordu: "yarın" takvimi seçiyor, `"at "`
kalıbı sondaki boşluk yüzünden cümle sonunda eşleşmediği için niyet de okumaya düşüyordu — yani
mail taslağı yerine takvim okunuyordu. Ayrıca `"at "` alt dize olarak arandığı için *"sanat
etkinliği"* yazma niyeti sayılıyordu.

Araç seçimi ağırlıklı puanlamaya geçirildi: kesin belirleyici kelimeler (takvim, gelen kutusu)
2 puan, başka bir aracın konusu olabilecek zayıf ipuçları (toplantı, yarın) 1 puan, e-posta
adresi 3 puan. Kısa ve başka kelimelerin içinde geçebilen fiiller (`at`, `yaz`, `ilet`) tam
kelime olarak aranıyor.

**8.2 Takvim taslağında tarih ayrıştırma.** Yalnızca "yarın" tanınıyordu. Tanınmayan her ifade
sessizce **bugüne** düşüyor ve ifadenin kendisi başlığa sızıyordu: *"Perşembe 14:00 diş randevusu
ekle"* → bugün, başlık `"Perşembe  diş"`. Artık hafta günleri (geçmişse gelecek haftaya taşınarak),
"öbür gün", "N gün sonra", "haftaya", "25 Ağustos", "saat 9", sabah/öğlen/akşam ve süre
("2 saatlik") çözülüyor; başlık tarih ve fiil artıklarından temizleniyor. 24 birim testi eklendi.

Not: bu hata veri kaybettirmiyordu, çünkü onay kapısı taslağı tarihiyle birlikte kullanıcıya
gösteriyor. Yine de yazma yolundaki her sessiz varsayım risklidir.

**8.3 Web arayüzünün internet bağımlılığı.** `ui/web.py` ikon fontunu bir CDN'den çekiyordu.
Projenin temel iddiası "tamamen internetsiz" olduğu hâlde arayüz ağsız ortamda ikonlarını
kaybediyordu. İkonlar gömülü SVG'ye çevrildi; dış bağımlılık kalmadı.

### Aynı incelemede eklenen iyileştirmeler

- **Cevap akışı.** p95 gecikme 12 saniyeye kadar çıkabiliyor ve ekran o süre boyunca boş
  kalıyordu. `llm.chat_stream()` ile cevap geldikçe yazılıyor; ölçülen süre değişmiyor, algılanan
  süre belirgin düşüyor.
- **Çok turlu konuşma.** Son iki tur isteme ekleniyor; işaret zamiri içeren takip soruları
  ("peki onu nasıl kapatırım?") erişim için önceki soruyla genişletiliyor. Uzunluğa değil zamire
  bakılıyor ki kendi başına anlamlı kısa sorular ("RAG nedir?") bozulmasın.
- **Otomatik kalite puanı.** Elle puanlama tekrarlanabilir değildi; `expected_substrings` ile
  otomatikleşti.

### Ölçüm dışı kalan
Bir şey de bilerek düzeltilmedi: erişimde her sorguda 58 parça SQLite'tan okunup JSON çözülüyor.
Ölçüldü, **10 ms** sürüyor — darboğaz tamamen modelde olduğu için önbellek eklemek gereksiz
karmaşıklık olurdu.

---

## 9. Hibrit erişim ve yazım hatası toleransı

Kullanıcı isteği üzerine erişim katmanı yazım hatalarına dayanıklı hâle getirildi. Embedding
araması bozuk yazımda zayıflıyor: "bölgden" ile "bölgeden" farklı alt-parçalara ayrıldığı için
vektörler uzaklaşıyor.

**Çözüm.** `app/lexical.py` metni sadeleştiriyor (Türkçe karakterler ASCII'ye, noktalama atılıyor)
ve sorgu kelimelerini metindeki kelimelerle `difflib` üzerinden bulanık karşılaştırıyor. Skor
harmanlanıyor: `0.75 × kosinüs + 0.25 × sözlüksel`. Sadeleştirme yalnızca sözlüksel katmanda
uygulanıyor; sorgu embedding'e ham hâliyle gidiyor, çünkü çok dilli model Türkçe karakterlerle
eğitilmiş.

**Ölçüm.** 14 cevaplanabilir sorunun bozuk yazımlı hâli (`yazim_hatasi` kategorisi) eklendi:

| Yapılandırma | İsabet | Yazım hatalı isabet | Çekimserlik |
|---|---|---|---|
| Yalnız kosinüs (en iyi eşik 0.38) | 14/14 | 12/14 | 5/6 |
| **Hibrit, eşik 0.34 (seçilen)** | **14/14** | **13/14** | **6/6** |

Sözlüksel katman iki cephede birden kazandırıyor: bozuk yazımda bir soru daha yakalanıyor ve
cevaplanamaz sorularda çekimserlik tamamlanıyor. Eşiği tek başına düşürerek aynı yazım kazancını
elde etmek mümkün ama bedeli ağır: yalnız kosinüsle eşik 0.30'a indirildiğinde çekimserlik
2/6'ya çöküyor.

Kaçan iki soru: `RAGin uc adimi nedir?` (skor 0.26; "RAG" kısaltması bozulunca ne anlam ne de
kelime tutuyor) ve kısmen `Yarım kalan degisiklikleri...` sorusu.

---

## 10. İki ölçüm hatası

**10.1 Ölçüm, uygulamanın skorunu kullanmıyordu.** `scripts/evaluate.py` içindeki
`score_questions` yalnızca kosinüs hesaplıyordu; hibrit skor uygulamaya girdikten sonra bile
taramalar eski formülü ölçmeye devam etti. İlk "hibrit" sonuçları bu yüzden yanlıştı (0.38 eşiği
seçilmişti). Düzeltmeden sonra doğru eşik 0.34 çıktı ve üç ölçütte birden daha iyi sonuç verdi.
Ders: ölçüm aracı, ölçtüğü kodu **çağırmalı**, kopyalamamalı.

**10.2 Üretim sınırı yoktu, sonra fazla genişti.** `max_tokens` başta hiç ayarlanmamıştı; sonra
1200 yapıldı. Ölçüm, belirsiz sorularda modelin 4000+ karakter yazıp yanıtı **48 saniyeye**
çıkardığını gösterdi. Doğru cevaplar 200-600 karakter sürüyor. Sınır 450 belirtece çekildi ve
isteme "en fazla birkaç cümle" kuralı eklendi:

| | Önce | Sonra |
|---|---|---|
| Otomatik kalite | 26/28 | **28/28** |
| Ortalama süre | 10,9 sn | **4,6 sn** |
| p95 süre | 48,2 sn | **10,3 sn** |

Kaliteyi de yükseltmesi beklenmiyordu: sınır, modeli konudan sapmadan cevaplamaya zorluyor.

---

## 11. Arayüz değişikliğinden sonraki nihai durum

| Metrik | Sonuç |
|---|---|
| Sohbet modeli | `phi-4-mini` (Foundry Local) |
| Yönlendirme doğruluğu | 6/6 (%100) |
| Erişim isabeti hit@3 | 14/14 (%100) |
| Yazım hatalı sorularda erişim | 13/14 (%93) |
| Otomatik kalite puanı | 28/28 (%100) |
| Cevaplanamazda çekimserlik | 6/6 (%100) |
| Ortalama / p50 / p95 süre | 4,60 sn / 4,50 sn / 10,27 sn |
| Uç durumlarda çökme | 0 |
| Test paketi | 167 test, tamamı geçiyor |

---

## 12. Kısa sorgular ve Foundry Local yükseltmesi (21 Ağustos 2026)

### 12.1 Ölçülmeyen bir soru biçimi: kısa sorgular

Arayüz kullanılırken "git stash ne işe yarar?" sorusuna asistan **"bilgim yok"** dedi. Doğru parça
sıralamada birinciydi ama skoru 0,243 ile eşiğin altındaydı: embedding kısa sorgularda zayıf kalıyor
(kosinüs 0,157), sözlüksel katman ise tek başına eşiği geçmeye yetmiyordu.

Soru setinin tamamı **tam cümlelerden** oluştuğu için bu biçim hiç ölçülmemişti. `kisa_sorgu`
kategorisi eklendi (6 sorgu: "ls -la", "sanal ortam", "foundry model unload", …) ve iki düzeltme
yapıldı:

1. **Sözlüksel kurtarma kuralı** (`retriever.accepts`): kelimelerin en az yarısı tutuyorsa ve
   anlamsal yakınlık tabanın üstündeyse (`dense ≥ 0,10`) parça eşiğin altında da kabul edilir.
2. **İki harfli kelimeler artık atılmıyor.** `lexical.tokens` en az 3 harfli kelimeleri alıyordu;
   "ls -la" sorgusunda tüm bilgi iki harfli kelimelerdeydi ve sözlüksel skor sıfır çıkıyordu.
   Sınır 2 harfe indirildi, anlam taşımayan kısa kelimeler (`de`, `da`, `ki`, `bu`, …) açık bir
   listeyle elendi.

| Ölçüt | Önce | Sonra |
|---|---|---|
| Erişim isabeti | 14/14 | 14/14 |
| Yazım hatalı sorularda erişim | 13/14 | **14/14** |
| Kısa sorgularda erişim | (ölçülmüyordu) 4/6 | **6/6** |
| Cevaplanamazda çekimserlik | 6/6 | 6/6 |

Ders: bir ölçüt kümesi yalnızca içindeki soru biçimlerini korur. Gerçek kullanımda ortaya çıkan
her yeni biçim, düzeltmeden önce sete eklenmelidir.

### 12.2 Foundry Local 0.8.119 → 0.10.3

Görsel yükleme için yapılan yükseltme üç şey değiştirdi:

- **Görsel modeller artık yükleniyor.** `qwen3-vl-2b-instruct` 0.8'de `genai_config.json`
  ayrıştırma hatasıyla açılmıyordu; 0.10.3'te sorunsuz yükleniyor.
- **Boşta kalma davranışı ayara taşındı.** 0.8'de model 600 saniye hareketsizlikte bellekten
  atılıyor ve sonraki ilk soru ~30 saniye sürüyordu. 0.10.3'te `idle-timeout-minutes` varsayılan
  olarak **disabled**; sorun kaynağında çözülmüş oldu.
- **CLI komut yüzeyi kırıldı.** `foundry service status` → `foundry server status`, `--ttl`
  kaldırıldı, çıktılar `-o json` ile alınabiliyor. Uygulama her iki sürümle de çalışacak biçimde
  uyarlandı (`llm._discover_base_url`, `models.cache_entries`).

Yükseltme öncesi/sonrası aynı soru setiyle karşılaştırma (phi-4-mini):

| Metrik | 0.8.119 | 0.10.3 |
|---|---|---|
| Otomatik kalite | 28/28 | 28/28 |
| Çekimserlik | 6/6 | 6/6 |
| Ortalama süre | 4,66 sn | 4,32 sn |
| p50 | 4,64 sn | **3,38 sn** |
| p95 | 8,68 sn | 14,86 sn |
| Hata / çökme | 0 | 0 |

Kalite ve güvenilirlik aynı, tipik gecikme iyileşti; p95 tek bir uzun cevaptan etkilendi.

### 12.3 Görsel yükleme neden hâlâ kapalı

Model yüklendikten sonra görsel gönderildiğinde istek hata vermiyor, ama cevaplar modelin görüntüyü
değil **gönderilen JSON'u metin olarak** gördüğünü ortaya koydu:

> *"The image contains a list of metadata, including text and an image URL…"*

Kontrol olarak görselsiz, yalnız metinden oluşan aynı istek gönderildiğinde model "sol yarı beyaz"
diye cevap üretti — yani ortada görüntü yokken de aynı biçimde uyduruyor. Sonuç: Foundry Local'in
yerel OpenAI uç noktası içerik dizisini düz metne indirgiyor ve görseli modele iletmiyor. Bu bizim
tarafımızdan kapatılabilecek bir eksik değil; özellik kod tarafında hazır bekletiliyor.


---

## 13. Sadakat ölçümü ve satır içi atıflar (25 Ağustos 2026)

Bölüm 7'nin birinci maddesi, phi-4-mini'nin bağlam dışına çıkabildiğini ama kullanıcının bunu
"kaynak gösterilmemesinden" anlayacağını söylüyordu. Bu bir varsayımdı: kaynak gösterilen bir cevap
da bağlam dışından gelebilir. Ölçülmeyen tek şey RAG'in asıl iddiasıydı — *cevap getirilen parçaya
dayanıyor mu*. Bu bölüm o boşluğu kapatıyor.

### 13.1 Ölçüt

`app/grounding.py`, cevaptaki içerik kelimelerinin kaçının bağlamda (yaklaşık olarak) geçtiğini
hesaplar. Model gerektirmez, koşum süresine eklenmez. İki eleme yapılır:

- **Sorudan gelen kelimeler** sayılmaz; yoksa soruyu tekrarlayan cevap haksız yere yüksek alır.
- **Modelin kendi cümle kurma kelimeleri** sayılmaz ("kullanın", "komutunu", "yapmak"…). Türkçe
  çekim ekleri yüzünden tam kelime yerine gövde başlangıcı eşleştirilir.

İkinci eleme ilk koşumdan sonra eklendi ve ölçütün kendi kusurunu düzeltti: C04'ün cevabı
``` `ls -la` komutunu kullanın. ``` — komut bağlamdan geliyor, ama "komutunu/kullanın" bağlamda
geçmediği için 0,50 alıyordu. Ortalama sadakat, bu düzeltmeyle **%67'den %80'e** çıktı; değişen
model ya da cevap değil, ölçütün gürültüsüydü.

### 13.2 Sonuçlar (phi-4-mini, 58 parça, 25 Ağustos)

| Metrik | Değer |
|---|---|
| Sadakat (ortalama) | %80 — 16 cevapta ölçüldü |
| Kod sadakati | 10/10 cevapta uydurulmuş komut yok |
| Eşik (0,60) altında | 2 cevap |

Diğer metrikler değişmedi: yönlendirme 6/6, erişim 14/14, yazım hatalı 14/14, kısa sorgu 6/6,
çekimserlik 6/6, kalite 28/28, p50 3,0 sn, p95 6,7 sn.

Eşiğin altında kalan iki cevap da uç durum kategorisinden:

| ID | Soru | Sadakat | Bağlamda karşılığı olmayan kelimeler |
|---|---|---|---|
| U02 | "git" (tek kelime) | 0,17 | ilgili, olduğunu, fazla, varsa, bildirin |
| U04 | "hem git hem python hem sqlite… nereden başlayayım" | 0,31 | araçları, öğrenmek, sırayı, takip, temel |

İkisinde de model belgeye değil kendi bilgisine dayanıp genel tavsiye veriyor — yani ölçüt tam
olarak yakalaması gerekeni yakalıyor. %100'lük kalite puanının arkasında görünmeyen tek gerçek
boşluk buydu.

### 13.3 Satır içi atıflar ve neden isteme yazdırılmadı

Arayüzde her cümlenin sonunda dayandığı parçanın numarası çıkar; tıklanınca o parça açılıp
vurgulanır. İki yol vardı:

1. **İsteme kural eklemek** — model her cümleye `[1]` yazsın. Bedeli: istem uzar, çıktı token'ı
   artar, gecikme büyür. `max_tokens`'ı geniş bırakmanın p95'i 48 saniyeye çıkardığı bu projede
   ölçülmüştü (Bölüm 10). Ayrıca phi-4-mini boyutunda bir model numaraları karıştırır ve istem
   değiştiği için tüm kalite/çekimserlik koşumu geçersiz olurdu.
2. **Cevap üretildikten sonra çıkarmak** — `app/citations.py`, her cümleyi sadakat ölçümünün
   kullandığı aynı sözlüksel eşleştirmeyle en çok örtüşen parçaya bağlar.

İkincisi seçildi. Ölçülen maliyet: **cevap başına ~2,7 ms** (p50'nin binde biri); istem, çıktı ve
tüm ölçüm sonuçları değişmedi. Atıflar veritabanına yazılmaz — metin ve parçalar zaten saklandığı
için sayfa yenilendiğinde yeniden hesaplanır, şema değişikliği gerekmedi.

Bedeli dürüstçe: atıf modelin beyanı değil, bizim tahminimizdir. Eşiği geçemeyen cümle atıfsız
bırakılır — yanlış atıf, atıfsızlıktan kötüdür.

### 13.4 İki eşiğin ölçümle seçilmesi

İlk yazımda `GROUNDING_FLOOR` ve `CITE_THRESHOLD` benim kararımdı. Bu, projenin kendi kuralına
aykırıydı: `SIM_THRESHOLD` ve `TOP_K` tahminle değil taramayla seçilmişti ve raporun tamamı bunun
üzerine kurulu. Kayıtlı bir koşum JSON'u üzerinden her iki eşik de tarandı (model çağrılmaz):

```bash
python scripts/evaluate.py --sadakat-tarama docs/eval/sonuclar-20260825-1413-phi-4-mini.json
```

**Sadakat eşiği.** Ayrım iki grup üzerinden yapılır: `cevaplanabilir` cevaplar belgeye dayanmak
zorundadır (altına düşerse yanlış alarm), `uc_durum` cevaplarında model kendi bilgisine dayanır
(yakalanmalı).

| Eşik | Yanlış alarm | Yakalanan |
|---|---|---|
| 0,40 – 0,60 | 0/13 | 2/3 |
| 0,65 – 0,70 | 2/13 | 3/3 |
| 0,80 | 3/13 | 3/3 |

**0,60** seçildi: yanlış alarm vermeyen en yüksek değer. 0,65'e çıkmak üçüncü uç durumu yakalıyor
ama bedeli iki doğru cevabı düşük işaretlemek — dayanaksızlık iddiası yanlışsa ölçüt güvenilirliğini
kaybeder, o yüzden yanlış alarm sıfırda tutuldu.

**Atıf eşiği.** İlk denenen vekil ölçüt (atıfın beklenen kaynak dışına gitmesi) hiçbir eşikte
ayırt etmedi — her satırda 0. Erişim isabeti 14/14 olduğu için ilk parça neredeyse her zaman
beklenen kaynak; ölçüt kör. Yerine gerçek denge ölçüldü: `cevaplanabilir` cevaplarda kapsama
yüksek olmalı, `uc_durum` cevaplarında model doğaçlama yaptığı için atıf verilmemeli.

| Eşik | Kapsama (cevaplanabilir) | Doğaçlamaya atıf (uç durum) |
|---|---|---|
| 0,40 | 23/23 (%100) | 10/26 |
| 0,50 | 21/23 (%91) | 7/26 |
| **0,55** | **21/23 (%91)** | **6/26** |
| 0,60 | 21/23 (%91) | 6/26 |
| 0,70 | 18/23 (%78) | 6/26 |
| 0,80 | 15/23 (%65) | 6/26 |

**0,55** seçildi: eğrinin dirseği. 0,40'a inmek kapsamayı iki cümle artırıyor ama doğaçlama
cümlelerine verilen atıfı 6'dan 10'a çıkarıyor; 0,70'e çıkmak ise kapsamayı %78'e düşürüyor,
karşılığında doğaçlamaya atıf hiç azalmıyor. 0,55 ile 0,60 aynı sonucu verdiği için ikisinden
düşük olanı — yani daha kapsayıcı olanı — alındı.

Tarama çıktısı `docs/eval/esik-taramasi-*.md` altına yazılır.
