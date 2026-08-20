# Değerlendirme sonuçları — 20.08.2026 11:13

| Ayar | Değer |
|---|---|
| Sohbet modeli | `Phi-4-mini-instruct-generic-gpu:5` |
| Embedding modeli | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| TOP_K | 3 |
| SIM_THRESHOLD | 0.38 |
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
| C01 | Ekran görüntüsünü belirli bir bölgeden nasıl | macos-kisayollar.md | macos-kisayollar.md | 0.678 | ✅ |
| C02 | Git'te son commit'i geri alıp değişiklikleri | git-notlari.md | git-notlari.md | 0.673 | ✅ |
| C03 | Yarım kalan değişiklikleri geçici olarak nas | git-notlari.md | git-notlari.md | 0.430 | ✅ |
| C04 | Klasördeki gizli dosyaları da listeleyen kom | terminal-komutlar.md | terminal-komutlar.md, macos-kisayollar.md | 0.491 | ✅ |
| C05 | Bir dosyanın içinde metin aramak için hangi  | terminal-komutlar.md | terminal-komutlar.md | 0.449 | ✅ |
| C06 | Python'da sanal ortam nasıl oluşturulur ve e | python-notlari.md | python-notlari.md, vscode-notlari.md | 0.685 | ✅ |
| C07 | requirements.txt içindeki bağımlılıkları nas | python-notlari.md | python-notlari.md, rag-kavramlari.md | 0.479 | ✅ |
| C08 | SQLite'ta tablo zaten varsa hata almamak içi | sqlite-notlari.md | sqlite-notlari.md | 0.586 | ✅ |
| C09 | Embedding vektörleri SQLite'ta hangi biçimde | sqlite-notlari.md | sqlite-notlari.md, rag-kavramlari.md | 0.651 | ✅ |
| C10 | Foundry Local'de yüklü bir modeli bellekten  | foundry-local-notlari.md | foundry-local-notlari.md | 0.475 | ✅ |
| C11 | Foundry Local servisinin adresi neden koda g | foundry-local-notlari.md | foundry-local-notlari.md | 0.571 | ✅ |
| C12 | RAG'in üç adımı nedir? | rag-kavramlari.md | rag-kavramlari.md | 0.548 | ✅ |
| C13 | Benzerlik eşiği çok yüksek olursa ne olur? | rag-kavramlari.md | rag-kavramlari.md | 0.501 | ✅ |
| C14 | VS Code'da projenin tamamında nasıl arama ya | vscode-notlari.md | python-notlari.md, vscode-notlari.md | 0.501 | ✅ |

## Yazım hatalı sorularda erişim — 86% (12/14)

| ID | Bozuk yazımlı soru | Beklenen kaynak | En yüksek skor | Sonuç |
|---|---|---|---|---|
| H01 | Ekran görünütsünü belirli bir bölgden nasıl al | macos-kisayollar.md | 0.605 | ✅ |
| H02 | Gitte son commiti geri alıp değişikliklri nası | git-notlari.md | 0.630 | ✅ |
| H03 | Yarım kalan degisiklikleri gecici olarak nasil | git-notlari.md | 0.397 | ❌ |
| H04 | Klasordeki gizli dosyalari da listeleyn komut  | terminal-komutlar.md | 0.484 | ✅ |
| H05 | Bir dosyanin icinde metin aramk icin hangi kom | terminal-komutlar.md | 0.601 | ✅ |
| H06 | Pythonda sanal ortm nasil olusturulur? | python-notlari.md | 0.507 | ✅ |
| H07 | requirements.txt icindeki bagimliliklari nasil | python-notlari.md | 0.451 | ✅ |
| H08 | SQLitede tablo zatn varsa hata almamk icin ne  | sqlite-notlari.md | 0.637 | ✅ |
| H09 | Embeding vektorleri SQLitede hangi bicimde sak | sqlite-notlari.md | 0.677 | ✅ |
| H10 | Foundry Localde yuklu bir modeli bellekten nas | foundry-local-notlari.md | 0.512 | ✅ |
| H11 | Foundry Local servisinin adrsi neden koda gomu | foundry-local-notlari.md | 0.509 | ✅ |
| H12 | RAGin uc adimi nedir? | rag-kavramlari.md | 0.233 | ❌ |
| H13 | Benzerlik esigi cok yuksek olursa ne olur? | rag-kavramlari.md | 0.493 | ✅ |
| H14 | VS Codeda projenin tamaminda nasil arama yapar | vscode-notlari.md | 0.485 | ✅ |

## Çekimserlik (cevaplanamaz sorular) — 83% (5/6)

| ID | Soru | En yüksek skor | Eşiğin altında mı |
|---|---|---|---|
| B01 | Docker imajı nasıl oluşturulur? | 0.365 | ✅ |
| B02 | Kubernetes'te bir pod nasıl silinir? | 0.242 | ✅ |
| B03 | React'te useEffect kancası ne işe yarar? | 0.341 | ✅ |
| B04 | Excel'de düşeyara formülü nasıl yazılır? | 0.358 | ✅ |
| B05 | Ev kredisi faiz oranları nedir? | 0.207 | ✅ |
| B06 | Fotoğrafta diyafram değeri neyi etkiler? | 0.440 | ❌ |

## Üretim (uçtan uca cevaplar)

| Metrik | Değer |
|---|---|
| Soru sayısı | 24 |
| Ortalama süre | 8.70 sn |
| p50 süre | 4.32 sn |
| p95 süre | 46.05 sn |
| Cevaplanamazda çekimserlik | 6/6 |
|   — eşik sayesinde / model sayesinde | 6 / 0 |
| Hata / çökme | 0 |
| Otomatik kalite puanı | 26/28 (%93) |

Otomatik puan beklenen ifadelere bakar (2 = hepsi, 1 = bir kısmı, 0 = hiçbiri); elle puan sütunu gerekirse insan değerlendirmesi için boş bırakılmıştır.

| ID | Kategori | Soru | Cevap | Kaynaklar | Süre | Oto | Elle |
|---|---|---|---|---|---|---|---|
| C01 | cevaplanabilir | Ekran görüntüsünü belirli bir bölgeden n | Ekran görüntüsünü belirli bir bölgeden almak için Cmd + Shift + 4 tuşlarına basın, ardından seçilen bölgeyi se | macos-kisayollar.md | 6.01 | 2 |   |
| C02 | cevaplanabilir | Git'te son commit'i geri alıp değişiklik | `git reset --soft HEAD~1` kullanın. Bu, son commit'i geri alır ama dosyalara dokunmaz. Değişiklikler çalışma a | git-notlari.md | 4.93 | 2 |   |
| C03 | cevaplanabilir | Yarım kalan değişiklikleri geçici olarak | `git stash` kullanın. | git-notlari.md | 4.87 | 2 |   |
| C04 | cevaplanabilir | Klasördeki gizli dosyaları da listeleyen | `ls -la` komutunu kullanarak klasörde gizli dosyaları da listeleyebilirsiniz. | terminal-komutlar.md, macos-kisayollar.md, vscode-notlari.md | 5.66 | 2 |   |
| C05 | cevaplanabilir | Bir dosyanın içinde metin aramak için ha | `grep "aranacak-kelime" dosya.txt` | terminal-komutlar.md | 4.12 | 2 |   |
| C06 | cevaplanabilir | Python'da sanal ortam nasıl oluşturulur  | Sanal ortam oluşturmak için `python3 -m venv .venv` çalıştırın. Etkinleştirmek için terminalde `.venv/bin/acti | python-notlari.md, vscode-notlari.md | 46.05 | 2 |   |
| C07 | cevaplanabilir | requirements.txt içindeki bağımlılıkları | `pip install -r requirements.txt` kullanın. | python-notlari.md | 4.10 | 2 |   |
| C08 | cevaplanabilir | SQLite'ta tablo zaten varsa hata almamak | `CREATE TABLE IF NOT EXISTS` | sqlite-notlari.md | 4.33 | 2 |   |
| C09 | cevaplanabilir | Embedding vektörleri SQLite'ta hangi biç | JSON metni olarak `TEXT` sütununda ya da ikili veri olarak `BLOB` sütununda saklanır. | sqlite-notlari.md, rag-kavramlari.md | 4.32 | 2 |   |
| C10 | cevaplanabilir | Foundry Local'de yüklü bir modeli bellek | `foundry model unload model-adi` komutunu kullanarak Foundry Local'de yüklü bir modeli bellekten boşaltabilirs | foundry-local-notlari.md | 55.02 | 2 |   |
| C11 | cevaplanabilir | Foundry Local servisinin adresi neden ko | Adres koda gömülmemelidir çünkü Foundry Local dinamik bir yerel port kullanır. | foundry-local-notlari.md | 7.16 | 2 |   |
| C12 | cevaplanabilir | RAG'in üç adımı nedir? | Retrieve, Augment, Generate. | rag-kavramlari.md | 4.11 | 2 |   |
| C13 | cevaplanabilir | Benzerlik eşiği çok yüksek olursa ne olu | Benzerlik eşiği çok yüksek olursa, asistanin bildiği şeylere gelinmez. Bu durumda, asistan bilmediği şeylere g | rag-kavramlari.md | 4.32 | 0 |   |
| C14 | cevaplanabilir | VS Code'da projenin tamamında nasıl aram | Cmd + Shift + F kullanın. | vscode-notlari.md | 3.36 | 2 |   |
| B01 | cevaplanamaz | Docker imajı nasıl oluşturulur? | Belgelerimde bu konuda bilgi yok. | — | 0.14 | — |   |
| B02 | cevaplanamaz | Kubernetes'te bir pod nasıl silinir? | Belgelerimde bu konuda bilgi yok. | — | 0.08 | — |   |
| B03 | cevaplanamaz | React'te useEffect kancası ne işe yarar? | Belgelerimde bu konuda bilgi yok. | — | 0.09 | — |   |
| B04 | cevaplanamaz | Excel'de düşeyara formülü nasıl yazılır? | Belgelerimde bu konuda bilgi yok. | — | 0.09 | — |   |
| B05 | cevaplanamaz | Ev kredisi faiz oranları nedir? | Belgelerimde bu konuda bilgi yok. | — | 0.08 | — |   |
| B06 | cevaplanamaz | Fotoğrafta diyafram değeri neyi etkiler? | Belgelerimde bu konuda bilgi yok. | — | 0.11 | — |   |
| U01 | uc_durum | (boş) | Belgelerimde bu konuda bilgi yok. | — | 0.01 | — |   |
| U02 | uc_durum | git | `git stashes` kullanarak yarım kalan değişiklikleri geçici olarak saklayabilirsiniz. Geçici saklama yedeklenmi | git-notlari.md | 4.89 | — |   |
| U03 | uc_durum | nasıl? | Verilen bağlamda metni vektöre çevirin. Vektörler embeddisi metinler arasındaki anlamlılıkla karşılaştırılabil | rag-kavramlari.md | 44.11 | — |   |
| U04 | uc_durum | Bilgisayarımda hem git hem python hem sq | Belgelerimde bu konuda bilgi yok. | — | 0.83 | — |   |

