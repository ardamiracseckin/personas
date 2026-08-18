# RAG Kavramları

## RAG nedir

RAG (Retrieval-Augmented Generation, Erişimle Zenginleştirilmiş Üretim), bir dil modelinin cevabını kendi ezberine değil, dışarıdan getirilen belgelere dayandıran tasarım desenidir.

Üç adımdan oluşur: Retrieve (soruya en ilgili belge parçalarını bul), Augment (bu parçaları modelin istemine bağlam olarak ekle), Generate (model cevabı bu bağlamdan üretir).

## Neden gerekli

Dil modelleri eğitildikleri veride olmayan, kuruma veya kişiye özel bilgileri bilmez. Bilmediği bir şey sorulduğunda kendinden emin biçimde yanlış cevap üretmesine halüsinasyon denir.

RAG bu sorunu iki yönden azaltır: model cevabı elindeki gerçek metne dayandırır ve hangi belgeden yararlandığı gösterilebildiği için cevap doğrulanabilir hale gelir.

Modeli yeniden eğitmeye (fine-tuning) göre çok daha ucuzdur; bilgi güncellendiğinde yalnızca belgeler yeniden işlenir, model değişmez.

## Embedding

Embedding, bir metni anlamını temsil eden sayı dizisine (vektöre) çeviren modeldir. Anlamca yakın metinler vektör uzayında birbirine yakın düşer.

Bu sayede arama, kelime eşleşmesi yerine anlam eşleşmesiyle yapılabilir: "ekran görüntüsü nasıl alınır" sorusu, içinde bu kelimeler birebir geçmese de ilgili notu bulabilir.

Soru ve belgeler mutlaka aynı embedding modeliyle vektöre çevrilmelidir; farklı modellerin vektörleri karşılaştırılamaz.

## Kosinüs benzerliği

İki vektörün ne kadar benzediği genellikle kosinüs benzerliğiyle ölçülür. Değer aralığı -1 ile 1 arasındadır; 1'e yaklaşması anlamların örtüştüğünü gösterir.

Kosinüs benzerliği iki vektörün nokta çarpımının, uzunluklarının çarpımına bölünmesiyle hesaplanır. Vektörlerin uzunluğunu değil yönünü karşılaştırdığı için metin uzunluğundan az etkilenir.

Küçük veri kümelerinde tüm vektörlerle tek tek karşılaştırma yapmak (kaba kuvvet arama) yeterlidir ve ek bir kütüphane gerektirmez.

## Parçalama (chunking)

Belgeler bütün halinde değil, parçalar halinde saklanır. Tipik parça boyutu bir ila üç paragraftır.

Parça çok büyük olursa içine konuyla ilgisiz metin karışır ve modelin dikkati dağılır. Çok küçük olursa cevabı vermeye yetecek bağlam kalmaz.

Parçanın hangi başlık altında olduğunu parçaya eklemek, hem benzerlik skorunu hem de cevabın bağlamını güçlendirir.

## Top-K ve benzerlik eşiği

Arama sonucunda en yüksek skorlu K parça alınır; küçük bilgi tabanlarında K genellikle 2 ile 5 arasındadır.

Skoru belirlenen eşiğin altında kalan parçalar tamamen elenir. Eşik, asistanın "bilmiyorum" diyebilmesini sağlayan mekanizmadır: eşiği geçen parça yoksa modele hiç soru sorulmadan bilgi bulunamadığı bildirilir.

Eşik çok yüksek olursa asistan bildiği şeylere de bilmiyorum der; çok düşük olursa alakasız parçalarla uydurma cevap üretir. Doğru değer tahminle değil, hazırlanan soru setiyle ölçülerek belirlenir.

## İstem (prompt) tasarımı

Sistem istemi modele rolünü ve kurallarını söyler. RAG için üç kural kritiktir: yalnızca verilen bağlamı kullan, bağlamda yoksa bilmediğini söyle, kullanılan kaynağı belirt.

Kullanıcı istemi genellikle "BAĞLAM: ...\n\nSORU: ..." biçiminde kurulur; bağlamın soruyla karışmaması için açık etiketler kullanılır.

Küçük modellerde talimatlar kısa, net ve emir kipinde olmalıdır; uzun ve koşullu talimatlar takip edilmez.

## Değerlendirme

Bir RAG sisteminin başarısı iki ayrı katmanda ölçülür: erişim katmanı doğru parçayı buluyor mu, üretim katmanı bulunan parçadan doğru cevap yazıyor mu.

Erişim başarısı, beklenen kaynağın ilk K sonuç içinde çıkma oranıyla (hit@K) ölçülür ve dil modeli çalıştırılmadan hesaplanabilir.

Cevaplanamaz sorular da test setine konmalıdır; sistemin bunlarda uydurma yapmayıp bilmediğini söyleme oranı en az doğru cevap oranı kadar önemlidir.
