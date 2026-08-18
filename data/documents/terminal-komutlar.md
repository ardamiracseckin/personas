# Terminal Komutları

## Gezinme

Bulunduğun klasörün tam yolunu göstermek için `pwd` çalıştırılır.

Klasördeki dosyaları listelemek için `ls`, gizli dosyalar ve ayrıntılarla birlikte listelemek için `ls -la` kullanılır. Boyutları okunabilir biçimde görmek için `ls -lh` yazılır.

Başka bir klasöre geçmek için `cd klasor-yolu` kullanılır. Bir üst klasöre çıkmak için `cd ..`, ev klasörüne dönmek için tek başına `cd` yeterlidir.

## Dosya işlemleri

Dosya kopyalamak için `cp kaynak hedef`, klasörü içeriğiyle kopyalamak için `cp -r kaynak hedef` kullanılır.

Dosya taşımak veya yeniden adlandırmak için `mv eski-ad yeni-ad` kullanılır.

Bir dosyayı silmek için `rm dosya-adi` yazılır; bu işlem çöp kutusuna göndermez, geri alınamaz. Klasörü içeriğiyle silmek için `rm -rf klasor` kullanılır ve bu komut çok dikkatli kullanılmalıdır.

Yeni klasör oluşturmak için `mkdir klasor-adi`, iç içe klasörler için `mkdir -p a/b/c` kullanılır.

## Dosya içeriğini görüntüleme

Kısa bir dosyanın tamamını yazdırmak için `cat dosya.txt` kullanılır.

Uzun bir dosyayı sayfa sayfa okumak için `less dosya.txt` kullanılır; çıkmak için `q` tuşuna basılır.

İlk on satır için `head dosya.txt`, son on satır için `tail dosya.txt` kullanılır. Bir kayıt dosyasını canlı izlemek için `tail -f gunluk.log` yazılır.

## Arama

Bir dosya içinde metin aramak için `grep "aranacak-kelime" dosya.txt` kullanılır. Klasörün tamamında, alt klasörler dahil aramak için `grep -r "kelime" .` yazılır.

Büyük-küçük harf ayrımı olmadan aramak için `-i`, eşleşmenin satır numarasını görmek için `-n` seçeneği eklenir: `grep -rin "kelime" .`

Ada göre dosya bulmak için `find . -name "*.md"` kullanılır.

## Süreçler

Çalışan işlemleri canlı izlemek için `top` kullanılır; daha okunaklı bir alternatif `htop` programıdır.

Belirli bir işlemi aramak için `ps aux | grep isim` kullanılır. Bir işlemi sonlandırmak için `kill PID`, yanıt vermiyorsa `kill -9 PID` yazılır.

Bir portu hangi işlemin dinlediğini bulmak için `lsof -i :8501` kullanılır.

## Borular ve yönlendirme

Komut çıktısını başka bir komuta aktarmak için boru işareti kullanılır: `ls -la | grep ".md"`.

Çıktıyı dosyaya yazmak için `>` (üzerine yazar), sonuna eklemek için `>>` kullanılır: `ls > liste.txt`.

Çıktıyı hem ekranda görmek hem dosyaya yazmak için `komut | tee dosya.txt` kullanılır.

## İzinler ve diğer araçlar

Bir betiği çalıştırılabilir yapmak için `chmod +x betik.sh` kullanılır.

Dosya ve klasör boyutlarını görmek için `du -sh *`, disk doluluğunu görmek için `df -h` kullanılır.

Klasörü arşivlemek için `tar -czf arsiv.tar.gz klasor`, açmak için `tar -xzf arsiv.tar.gz` kullanılır.

macOS'te bir dosyayı varsayılan uygulamasıyla açmak için `open dosya.pdf`, bulunulan klasörü Finder'da açmak için `open .` kullanılır.
