# VS Code Notları

## Komut paleti

VS Code'da neredeyse her işlem komut paletinden yapılabilir. Paleti açmak için Cmd + Shift + P kullanılır ve komut adı yazılır.

Dosya adına göre hızlı dosya açmak için Cmd + P kullanılır. Aynı kutuda satır numarasına gitmek için iki nokta üst üste, sembole gitmek için @ işareti kullanılır.

## Düzenleme

Aynı anda birden çok yere yazmak için Option tuşu basılıyken istenen noktalara tıklanır; her tıklama yeni bir imleç ekler.

Seçili kelimenin bir sonraki eşleşmesini de seçmek için Cmd + D kullanılır; art arda basıldığında birden çok eşleşme birlikte düzenlenir.

Satırı yukarı veya aşağı taşımak için Option + Yukarı/Aşağı ok, satırı kopyalamak için Shift + Option + Yukarı/Aşağı kullanılır.

Satırı yorum satırı yapmak veya yorumdan çıkarmak için Cmd + / kullanılır.

## Arama

Açık dosyada aramak için Cmd + F, değiştirmek için Cmd + Option + F kullanılır.

Projenin tamamında aramak için Cmd + Shift + F kullanılır. Arama kutusundaki simgelerle büyük-küçük harf duyarlılığı, tam kelime eşleşmesi ve düzenli ifade modu açılabilir.

Belirli klasörleri aramanın dışında tutmak için arama panelindeki "files to exclude" alanına örneğin `.venv, node_modules` yazılır.

## Terminal

Gömülü terminali açıp kapatmak için Control + ` (backtick) kullanılır. Yeni bir terminal sekmesi için Control + Shift + `.

Terminal proje kökünde açılır; sanal ortam etkinleştirildikten sonra çalıştırılan komutlar projenin bağımlılıklarını kullanır.

## Python ile çalışma

Python uzantısı kurulduğunda sağ alt köşedeki yorumlayıcı göstergesinden sanal ortam seçilir. Projede `.venv` varsa VS Code genellikle onu otomatik önerir.

Test paneli pytest testlerini keşfeder ve tek tek çalıştırmayı sağlar. Bir testin yanındaki oynat simgesiyle yalnızca o test çalıştırılabilir.

Hata ayıklamak için satır numarasının soluna tıklanarak kesme noktası konur ve F5 ile hata ayıklayıcı başlatılır. Adım adım ilerlemek için F10, fonksiyonun içine girmek için F11 kullanılır.

## Git entegrasyonu

Sol kenardaki kaynak denetimi panelinde değişen dosyalar listelenir; dosyaya tıklandığında değişiklikler yan yana karşılaştırmalı görünür.

Dosyanın yanındaki artı simgesi değişikliği sahneler, üstteki kutuya mesaj yazıp onay tuşuna basmak commit eder.

Bir satırın hangi commit'te değiştiğini görmek için GitLens gibi bir uzantı kullanılır.

## Ayarlar ve görünüm

Ayarları açmak için Cmd + Virgül kullanılır. Ayarlar hem arayüzden hem de JSON dosyasından düzenlenebilir.

Kenar çubuğunu gizleyip kod alanını genişletmek için Cmd + B kullanılır. Dikkat dağıtmayan tam odak modu için Cmd + K ardından Z tuşlarına basılır.

Dosyayı kaydederken otomatik biçimlendirme için ayarlardan "Format On Save" seçeneği açılır.
