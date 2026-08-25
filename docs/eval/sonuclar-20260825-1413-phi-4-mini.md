# Değerlendirme sonuçları — 25.08.2026 14:13

| Ayar | Değer |
|---|---|
| Sohbet modeli | `phi-4-mini` |
| Embedding modeli | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| TOP_K | 3 |
| SIM_THRESHOLD | 0.34 |
| Bilgi tabanı | 58 parça / 8 belge |

## Yönlendirme doğruluğu — 100% (6/6)

| ID | Soru | Beklenen | Gelen | Sonuç |
|---|---|---|---|---|
| Y01 | Bugün takvimimde ne var? | calendar/read | calendar/read | ✅ |
| Y02 | Yarın 15:00 dişçi randevusu ekle | calendar/write | calendar/write | ✅ |
| Y03 | Okunmamış maillerim neler? | mail/read | mail/read | ✅ |
| Y04 | ali@example.com adresine 'Rapor' konulu mail gön | mail/write | mail/write | ✅ |
| Y05 | Spotify aç | app/open | app/open | ✅ |
| Y06 | Ekran görüntüsü almanın kısayolu ne? | documents/read | documents/read | ✅ |

## Erişim isabeti (hit@3) — 100% (14/14)

| ID | Soru | Beklenen kaynak | Getirilen | En yüksek skor | Sonuç |
|---|---|---|---|---|---|
| C01 | Ekran görüntüsünü belirli bir bölgeden nasıl | macos-kisayollar.md | macos-kisayollar.md | 0.634 | ✅ |
| C02 | Git'te son commit'i geri alıp değişiklikleri | git-notlari.md | git-notlari.md | 0.671 | ✅ |
| C03 | Yarım kalan değişiklikleri geçici olarak nas | git-notlari.md | git-notlari.md | 0.423 | ✅ |
| C04 | Klasördeki gizli dosyaları da listeleyen kom | terminal-komutlar.md | terminal-komutlar.md, macos-kisayollar.md, vscode-notlari.md | 0.535 | ✅ |
| C05 | Bir dosyanın içinde metin aramak için hangi  | terminal-komutlar.md | terminal-komutlar.md | 0.453 | ✅ |
| C06 | Python'da sanal ortam nasıl oluşturulur ve e | python-notlari.md | python-notlari.md, vscode-notlari.md | 0.639 | ✅ |
| C07 | requirements.txt içindeki bağımlılıkları nas | python-notlari.md | python-notlari.md | 0.484 | ✅ |
| C08 | SQLite'ta tablo zaten varsa hata almamak içi | sqlite-notlari.md | sqlite-notlari.md | 0.627 | ✅ |
| C09 | Embedding vektörleri SQLite'ta hangi biçimde | sqlite-notlari.md | sqlite-notlari.md, rag-kavramlari.md | 0.631 | ✅ |
| C10 | Foundry Local'de yüklü bir modeli bellekten  | foundry-local-notlari.md | foundry-local-notlari.md | 0.464 | ✅ |
| C11 | Foundry Local servisinin adresi neden koda g | foundry-local-notlari.md | foundry-local-notlari.md | 0.642 | ✅ |
| C12 | RAG'in üç adımı nedir? | rag-kavramlari.md | rag-kavramlari.md | 0.561 | ✅ |
| C13 | Benzerlik eşiği çok yüksek olursa ne olur? | rag-kavramlari.md | rag-kavramlari.md | 0.626 | ✅ |
| C14 | VS Code'da projenin tamamında nasıl arama ya | vscode-notlari.md | vscode-notlari.md, python-notlari.md | 0.467 | ✅ |

## Yazım hatalı sorularda erişim — 100% (14/14)

| ID | Bozuk yazımlı soru | Beklenen kaynak | En yüksek skor | Sonuç |
|---|---|---|---|---|
| H01 | Ekran görünütsünü belirli bir bölgden nasıl al | macos-kisayollar.md | 0.620 | ✅ |
| H02 | Gitte son commiti geri alıp değişikliklri nası | git-notlari.md | 0.629 | ✅ |
| H03 | Yarım kalan degisiklikleri gecici olarak nasil | git-notlari.md | 0.344 | ✅ |
| H04 | Klasordeki gizli dosyalari da listeleyn komut  | terminal-komutlar.md | 0.488 | ✅ |
| H05 | Bir dosyanin icinde metin aramk icin hangi kom | terminal-komutlar.md | 0.524 | ✅ |
| H06 | Pythonda sanal ortm nasil olusturulur? | python-notlari.md | 0.530 | ✅ |
| H07 | requirements.txt icindeki bagimliliklari nasil | python-notlari.md | 0.463 | ✅ |
| H08 | SQLitede tablo zatn varsa hata almamk icin ne  | sqlite-notlari.md | 0.692 | ✅ |
| H09 | Embeding vektorleri SQLitede hangi bicimde sak | sqlite-notlari.md | 0.675 | ✅ |
| H10 | Foundry Localde yuklu bir modeli bellekten nas | foundry-local-notlari.md | 0.456 | ✅ |
| H11 | Foundry Local servisinin adrsi neden koda gomu | foundry-local-notlari.md | 0.562 | ✅ |
| H12 | RAGin uc adimi nedir? | rag-kavramlari.md | 0.300 | ✅ |
| H13 | Benzerlik esigi cok yuksek olursa ne olur? | rag-kavramlari.md | 0.619 | ✅ |
| H14 | VS Codeda projenin tamaminda nasil arama yapar | vscode-notlari.md | 0.471 | ✅ |

## Kısa sorgularda erişim — 100% (6/6)

| ID | Sorgu | Beklenen kaynak | En yüksek skor | Sonuç |
|---|---|---|---|---|
| K01 | git stash ne işe yarar? | git-notlari.md | 0.243 | ✅ |
| K02 | ls -la | terminal-komutlar.md | 0.561 | ✅ |
| K03 | sanal ortam | python-notlari.md | 0.525 | ✅ |
| K04 | foundry model unload | foundry-local-notlari.md | 0.769 | ✅ |
| K05 | kosinüs benzerliği | rag-kavramlari.md | 0.633 | ✅ |
| K06 | ekran görüntüsü kısayolu | macos-kisayollar.md | 0.754 | ✅ |

## Çekimserlik (cevaplanamaz sorular) — 100% (6/6)

| ID | Soru | En yüksek skor | Eşiğin altında mı |
|---|---|---|---|
| B01 | Docker imajı nasıl oluşturulur? | 0.274 | ✅ |
| B02 | Kubernetes'te bir pod nasıl silinir? | 0.182 | ✅ |
| B03 | React'te useEffect kancası ne işe yarar? | 0.257 | ✅ |
| B04 | Excel'de düşeyara formülü nasıl yazılır? | 0.285 | ✅ |
| B05 | Ev kredisi faiz oranları nedir? | 0.205 | ✅ |
| B06 | Fotoğrafta diyafram değeri neyi etkiler? | 0.330 | ✅ |

## Üretim (uçtan uca cevaplar)

| Metrik | Değer |
|---|---|
| Soru sayısı | 24 |
| Ortalama süre | 3.38 sn |
| p50 süre | 3.21 sn |
| p95 süre | 6.62 sn |
| Cevaplanamazda çekimserlik | 6/6 |
|   — eşik sayesinde / model sayesinde | 6 / 0 |
| Hata / çökme | 0 |
| Otomatik kalite puanı | 28/28 (%100) |
| Sadakat (ortalama) | %80 — 16 cevapta ölçüldü |
| Kod sadakati | 10/10 cevapta uydurulmuş komut yok |

Otomatik puan beklenen ifadelere bakar (2 = hepsi, 1 = bir kısmı, 0 = hiçbiri); elle puan sütunu gerekirse insan değerlendirmesi için boş bırakılmıştır.

| ID | Kategori | Soru | Cevap | Kaynaklar | Süre | Oto | Sadakat | Elle |
|---|---|---|---|---|---|---|---|---|
| C01 | cevaplanabilir | Ekran görüntüsünü belirli bir bölgeden n | Ekran görüntüsünü belirli bir bölgeden almak için Cmd + Shift + 4 tuşlarına basın, ardından seçilen bölgeyi se | macos-kisayollar.md | 5.04 | 2 | 0.82 |   |
| C02 | cevaplanabilir | Git'te son commit'i geri alıp değişiklik | Son commit'i geri alıp değişiklikleri koruduğunuzda, `git reset --soft HEAD~1` komutunu kullanın. Bu, son comm | git-notlari.md | 5.89 | 2 | 0.75 |   |
| C03 | cevaplanabilir | Yarım kalan değişiklikleri geçici olarak | `git stash` kullanın. | git-notlari.md | 3.21 | 2 | 1.00 |   |
| C04 | cevaplanabilir | Klasördeki gizli dosyaları da listeleyen | `ls -la` komutunu kullanın. | terminal-komutlar.md, macos-kisayollar.md, vscode-notlari.md | 3.58 | 2 | 1.00 |   |
| C05 | cevaplanabilir | Bir dosyanın içinde metin aramak için ha | `grep "aranacak-kelime" dosya.txt` | terminal-komutlar.md | 3.04 | 2 | 1.00 |   |
| C06 | cevaplanabilir | Python'da sanal ortam nasıl oluşturulur  | Sanal ortam oluşturmak için `python3 -m venv .venv` çalıştırın. Etkinleştirmek için terminalinizi açın, `.venv | python-notlari.md, vscode-notlari.md | 6.62 | 2 | 0.63 |   |
| C07 | cevaplanabilir | requirements.txt içindeki bağımlılıkları | `pip install -r requirements.txt` kullanın. | python-notlari.md | 1.82 | 2 | 1.00 |   |
| C08 | cevaplanabilir | SQLite'ta tablo zaten varsa hata almamak | `CREATE TABLE IF NOT EXISTS` | sqlite-notlari.md | 3.13 | 2 | 1.00 |   |
| C09 | cevaplanabilir | Embedding vektörleri SQLite'ta hangi biç | JSON metni olarak `TEXT` sütununda veya ikili veri olarak `BLOB` sütununda saklanır. | sqlite-notlari.md, rag-kavramlari.md | 3.80 | 2 | 1.00 |   |
| C10 | cevaplanabilir | Foundry Local'de yüklü bir modeli bellek | `foundry model unload model-adi` komutunu kullanarak Foundry Local'de yüklü bir modeli bellekten boşaltabilirs | foundry-local-notlari.md | 6.36 | 2 | 0.64 |   |
| C11 | cevaplanabilir | Foundry Local servisinin adresi neden ko | Adres koda gömülmemelidir çünkü Foundry Local dinamik bir yerel port kullanır. | foundry-local-notlari.md | 3.40 | 2 | 0.83 |   |
| C12 | cevaplanabilir | RAG'in üç adımı nedir? | Retrieve, Augment, Generate. | rag-kavramlari.md | 2.17 | 2 | 1.00 |   |
| C13 | cevaplanabilir | Benzerlik eşiği çok yüksek olursa ne olu | Çok yüksek olursa 'Bilmiyorum' diyor. | rag-kavramlari.md | 2.62 | 2 | — |   |
| C14 | cevaplanabilir | VS Code'da projenin tamamında nasıl aram | VS Code'da projenin tamamında arama yapmak için Cmd + Shift + F kullanın. | vscode-notlari.md, python-notlari.md | 3.28 | 2 | 1.00 |   |
| B01 | cevaplanamaz | Docker imajı nasıl oluşturulur? | Belgelerimde bu konuda bilgi yok. | — | 0.11 | — | — |   |
| B02 | cevaplanamaz | Kubernetes'te bir pod nasıl silinir? | Belgelerimde bu konuda bilgi yok. | — | 0.09 | — | — |   |
| B03 | cevaplanamaz | React'te useEffect kancası ne işe yarar? | Belgelerimde bu konuda bilgi yok. | — | 0.10 | — | — |   |
| B04 | cevaplanamaz | Excel'de düşeyara formülü nasıl yazılır? | Belgelerimde bu konuda bilgi yok. | — | 0.10 | — | — |   |
| B05 | cevaplanamaz | Ev kredisi faiz oranları nedir? | Belgelerimde bu konuda bilgi yok. | — | 0.08 | — | — |   |
| B06 | cevaplanamaz | Fotoğrafta diyafram değeri neyi etkiler? | Belgelerimde bu konuda bilgi yok. | — | 0.09 | — | — |   |
| U01 | uc_durum | (boş) | Belgelerimde bu konuda bilgi yok. | — | 0.01 | — | — |   |
| U02 | uc_durum | git | Sorunun git ile ilgili olduğunu anladım. Lütfen daha fazla ayrıntı veya belirli bir git komutuna ihtiyacınız v | git-notlari.md | 3.77 | — | 0.17 |   |
| U03 | uc_durum | nasıl? | Verilen bağlamda metni vektöre çevirin:  Sorun: Nasıl yapılır?  Vektörler: [how_to_do_it]   Verilen bağlamda e | rag-kavramlari.md | 3.79 | — | 0.60 |   |
| U04 | uc_durum | Bilgisayarımda hem git hem python hem sq | Sorunuzun bağlamında hem git hem de python hem sqlite hem de Foundry Local kullanıyorsunuz. Bu araçları öğrenm | vscode-notlari.md, python-notlari.md | 19.12 | — | 0.31 |   |

### Sadakat (cevap getirilen parçaya mı dayanıyor)

Kalite puanı doğru bilginin cevapta geçip geçmediğine bakar; sadakat ise cevabın getirilen parçalardan mı yoksa modelin ezberinden mi geldiğini ölçer. Ölçüt sözlükseldir: cevaptaki içerik kelimelerinin kaçının bağlamda karşılığı var (sorudan gelen kelimeler sayılmaz). 0.60 altı ayrıca listelenir.

Eşiğin altında kalan 2 cevap:

| ID | Soru | Sadakat | Bağlamda karşılığı olmayan kelimeler |
|---|---|---|---|
| U02 | git | 0.17 | ilgili, oldugunu, fazla, varsa, bildirin |
| U04 | Bilgisayarımda hem git hem python hem sq | 0.31 | araclari, ogrenmek, sirayi, takip, baslayin, temel, dil, depolama |

### Kod sadakati (uydurulmuş komut var mı)

Ters tırnak içindeki her ifade bağlamda birebir geçmeli. Geçmiyorsa model komutu kendisi türetmiştir — kullanıcının çalıştıracağı yanlış komut budur.

Komut içeren 10 cevabın hepsinde komutlar bağlamdan geliyor; uydurulmuş komut yok.

