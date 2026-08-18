# Python Notları

## Sanal ortam

Projeye özel bir sanal ortam oluşturmak için `python3 -m venv .venv` çalıştırılır. Ortamı etkinleştirmek için `source .venv/bin/activate` kullanılır; çıkmak için `deactivate` yazılır.

Sanal ortam, projenin bağımlılıklarını sistem Python'ından ayırır. Etkin ortamda `which python` komutu `.venv/bin/python` yolunu göstermelidir.

## Paket yönetimi

Paket kurmak için `pip install paket-adi` kullanılır. Bir dosyadaki tüm bağımlılıkları kurmak için `pip install -r requirements.txt` yazılır.

Kurulu paketleri ve sürümlerini görmek için `pip list`, bunları dosyaya dökmek için `pip freeze > requirements.txt` kullanılır.

Bir paketi kaldırmak için `pip uninstall paket-adi` çalıştırılır.

## Proje yapısı

Bir Python paketi, içinde `__init__.py` bulunan klasördür. Modüller `from paket import modul` biçiminde içe aktarılır.

Bir dosya hem içe aktarılabilir hem doğrudan çalıştırılabilir olsun isteniyorsa `if __name__ == "__main__":` bloğu kullanılır. Modülü paket olarak çalıştırmak için `python -m paket.modul` yazılır.

## Veri yapıları

Liste kavraması (list comprehension) döngüyü tek satırda yazmayı sağlar: `kareler = [x * x for x in range(10)]`. Koşul eklenebilir: `[x for x in sayilar if x > 0]`.

Sözlük kavraması aynı mantıkla çalışır: `{k: len(k) for k in kelimeler}`.

Bir listeyi sıralamak için `liste.sort()` yerinde sıralar, `sorted(liste)` yeni liste döndürür. Sıralama ölçütü `key` ile verilir: `sorted(kayitlar, key=lambda r: r[2], reverse=True)`.

## Dosya okuma ve yazma

Dosyayı güvenli biçimde okumak için `with` bloğu kullanılır: `with open("dosya.txt", encoding="utf-8") as f: metin = f.read()`. Blok bitince dosya otomatik kapanır.

Yol işlemleri için `pathlib` tercih edilir: `from pathlib import Path` ile `Path("data") / "belgeler"` gibi platformdan bağımsız yollar kurulur. `path.read_text(encoding="utf-8")` dosyayı tek satırda okur.

Türkçe karakterlerin bozulmaması için okuma ve yazmada `encoding="utf-8"` açıkça belirtilmelidir.

## Hata yakalama

Hata yakalamak için `try` / `except` kullanılır. Yakalanan hata mesajına erişmek için `except Exception as e:` yazılır ve `e` metin olarak kullanılabilir.

Hangi hata olursa olsun çalışması gereken temizlik kodu `finally` bloğuna konur.

Kullanıcıya anlaşılır mesaj vermek için hata yakalanıp yeniden anlamlı bir mesajla `raise RuntimeError("açıklama")` biçiminde fırlatılabilir.

## JSON ve sözlükler

Python nesnesini JSON metnine çevirmek için `json.dumps(nesne)`, JSON metnini nesneye çevirmek için `json.loads(metin)` kullanılır. Dosyayla çalışırken `json.dump` ve `json.load` tercih edilir.

Türkçe karakterlerin kaçış dizisine dönüşmemesi için `json.dumps(nesne, ensure_ascii=False)` yazılır.

## Test

Testler `pytest` ile yazılır. Test dosyaları `test_` ile başlar, test fonksiyonları da `test_` ile başlar ve `assert` ifadesi kullanır.

Tüm testleri sessiz modda çalıştırmak için `python -m pytest -q` kullanılır. Tek bir dosyayı çalıştırmak için dosya yolu eklenir: `python -m pytest tests/test_router.py`.

Testte geçici klasör gerekiyorsa `tmp_path`, bir ayarı geçici olarak değiştirmek gerekiyorsa `monkeypatch` fixture'ları kullanılır.

## Biçimlendirme

Metin içine değişken gömmek için f-string kullanılır: `f"{ad} için {sayi} kayıt bulundu"`. Ondalık basamak sınırlamak için `f"{sure:.2f} saniye"` yazılır.

Uzun metinleri birleştirirken `"\n".join(satirlar)` yöntemi, döngüyle string toplamaktan hem hızlı hem okunaklıdır.
