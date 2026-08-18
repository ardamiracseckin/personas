# SQLite Notları

## SQLite nedir

SQLite, sunucusuz ve tek dosyalı bir SQL veritabanı motorudur. Ayrı bir servis kurmayı, port açmayı veya kullanıcı yönetmeyi gerektirmez; tüm veri tek bir `.db` dosyasında durur.

Bu özellikleri onu yerel uygulamalar, masaüstü araçları ve küçük veri kümeleri için ideal kılar. Dünyada en yaygın kullanılan veritabanı motorudur ve Python ile birlikte hazır gelir.

## Komut satırı

Bir veritabanını komut satırında açmak için `sqlite3 veritabani.db` çalıştırılır. Dosya yoksa oluşturulur.

Tabloları listelemek için `.tables`, bir tablonun şemasını görmek için `.schema tablo_adi` kullanılır. Çıkmak için `.quit` yazılır.

Sonuçları sütun başlıklarıyla okunaklı görmek için `.headers on` ve `.mode column` komutları verilir.

## Tablo oluşturma

Tablo `CREATE TABLE` ile oluşturulur. Tablo zaten varsa hata almamak için `CREATE TABLE IF NOT EXISTS` yazılır.

Örnek: `CREATE TABLE IF NOT EXISTS chunks (id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT NOT NULL, text TEXT NOT NULL, embedding TEXT NOT NULL);`

`INTEGER PRIMARY KEY AUTOINCREMENT` sütunu her yeni kayıtta otomatik artan benzersiz bir kimlik verir.

## Veri ekleme ve sorgulama

Kayıt eklemek için `INSERT INTO chunks(source, text) VALUES (?, ?)` kullanılır. Soru işaretleri parametre yer tutucusudur; değerler ayrı verilir.

Tüm kayıtları okumak için `SELECT * FROM chunks;`, belirli sütunları okumak için `SELECT source, text FROM chunks;` yazılır.

Koşul için `WHERE`, sıralama için `ORDER BY`, kayıt sayısını sınırlamak için `LIMIT` kullanılır: `SELECT text FROM chunks WHERE source = 'git-notlari.md' LIMIT 5;`

Kayıt sayısını öğrenmek için `SELECT COUNT(*) FROM chunks;`, gruplayarak saymak için `SELECT source, COUNT(*) FROM chunks GROUP BY source;` kullanılır.

Kayıt silmek için `DELETE FROM chunks;` tabloyu boşaltır; belirli kayıtlar için `WHERE` koşulu eklenir.

## Python ile kullanım

Python'da SQLite için ek kurulum gerekmez, `import sqlite3` yeterlidir.

Bağlantı `sqlite3.connect("veritabani.db")` ile açılır. `with baglanti:` bloğu kullanıldığında blok başarıyla biterse işlem otomatik olarak kaydedilir (commit), hata olursa geri alınır (rollback).

Sorgu `baglanti.execute("SELECT ...")` ile çalıştırılır; sonuçları almak için `fetchall()` (tüm satırlar) veya `fetchone()` (tek satır) kullanılır.

Parametreli sorgu her zaman tercih edilmelidir: `c.execute("INSERT INTO chunks(source, text) VALUES (?, ?)", (kaynak, metin))`. Değerleri metin birleştirmeyle sorguya gömmek SQL enjeksiyonuna açık kapı bırakır.

## Vektör saklama

SQLite'ın yerleşik bir vektör tipi yoktur. Embedding vektörleri ya JSON metni olarak `TEXT` sütununda ya da ikili veri olarak `BLOB` sütununda saklanır.

JSON yöntemi okunaklıdır ve hata ayıklaması kolaydır: kaydederken `json.dumps(vektor)`, okurken `json.loads(satir)` kullanılır.

Küçük veri kümelerinde benzerlik hesabı SQL'de değil Python tarafında yapılır: tüm vektörler belleğe okunur, kosinüs benzerliği hesaplanır ve en yüksek skorlu kayıtlar seçilir. Binlerce kaydın üzerine çıkıldığında özel vektör veritabanları veya SQLite eklentileri gerekir.

## Performans notları

Sık sorgulanan sütunlar için indeks oluşturulur: `CREATE INDEX idx_source ON chunks(source);`

Çok sayıda kayıt eklenirken her ekleme için ayrı bağlantı açmak yavaştır; tek bir işlem (transaction) içinde toplu ekleme yapmak belirgin hız kazandırır.
