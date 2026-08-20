# Değerlendirme sonuçları — 20.08.2026 11:09

| Ayar | Değer |
|---|---|
| Sohbet modeli | `phi-4-mini` |
| Embedding modeli | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| TOP_K | 3 |
| SIM_THRESHOLD | 0.2 |
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
| C02 | Git'te son commit'i geri alıp değişiklikleri | git-notlari.md | git-notlari.md, vscode-notlari.md | 0.673 | ✅ |
| C03 | Yarım kalan değişiklikleri geçici olarak nas | git-notlari.md | git-notlari.md | 0.430 | ✅ |
| C04 | Klasördeki gizli dosyaları da listeleyen kom | terminal-komutlar.md | terminal-komutlar.md, macos-kisayollar.md | 0.491 | ✅ |
| C05 | Bir dosyanın içinde metin aramak için hangi  | terminal-komutlar.md | terminal-komutlar.md | 0.449 | ✅ |
| C06 | Python'da sanal ortam nasıl oluşturulur ve e | python-notlari.md | python-notlari.md, vscode-notlari.md | 0.685 | ✅ |
| C07 | requirements.txt içindeki bağımlılıkları nas | python-notlari.md | python-notlari.md, rag-kavramlari.md, foundry-local-notlari.md | 0.479 | ✅ |
| C08 | SQLite'ta tablo zaten varsa hata almamak içi | sqlite-notlari.md | sqlite-notlari.md | 0.586 | ✅ |
| C09 | Embedding vektörleri SQLite'ta hangi biçimde | sqlite-notlari.md | sqlite-notlari.md, rag-kavramlari.md | 0.651 | ✅ |
| C10 | Foundry Local'de yüklü bir modeli bellekten  | foundry-local-notlari.md | foundry-local-notlari.md | 0.475 | ✅ |
| C11 | Foundry Local servisinin adresi neden koda g | foundry-local-notlari.md | foundry-local-notlari.md | 0.571 | ✅ |
| C12 | RAG'in üç adımı nedir? | rag-kavramlari.md | rag-kavramlari.md | 0.548 | ✅ |
| C13 | Benzerlik eşiği çok yüksek olursa ne olur? | rag-kavramlari.md | rag-kavramlari.md | 0.501 | ✅ |
| C14 | VS Code'da projenin tamamında nasıl arama ya | vscode-notlari.md | python-notlari.md, vscode-notlari.md | 0.501 | ✅ |

## Yazım hatalı sorularda erişim — 93% (13/14)

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
| H12 | RAGin uc adimi nedir? | rag-kavramlari.md | 0.233 | ✅ |
| H13 | Benzerlik esigi cok yuksek olursa ne olur? | rag-kavramlari.md | 0.493 | ✅ |
| H14 | VS Codeda projenin tamaminda nasil arama yapar | vscode-notlari.md | 0.485 | ✅ |

## Çekimserlik (cevaplanamaz sorular) — 0% (0/6)

| ID | Soru | En yüksek skor | Eşiğin altında mı |
|---|---|---|---|
| B01 | Docker imajı nasıl oluşturulur? | 0.365 | ❌ |
| B02 | Kubernetes'te bir pod nasıl silinir? | 0.242 | ❌ |
| B03 | React'te useEffect kancası ne işe yarar? | 0.341 | ❌ |
| B04 | Excel'de düşeyara formülü nasıl yazılır? | 0.358 | ❌ |
| B05 | Ev kredisi faiz oranları nedir? | 0.207 | ❌ |
| B06 | Fotoğrafta diyafram değeri neyi etkiler? | 0.440 | ❌ |

## Eşik / K taraması

| K | Eşik | İsabet | Yazım hatalı isabet | Çekimserlik | Denge |
|---|---|---|---|---|---|
| 3 | 0.20 | 100% | 93% | 0% | 64% |
| 3 | 0.25 | 100% | 86% | 33% | 73% |
| 3 | 0.30 | 100% | 86% | 33% | 73% |
| 3 | 0.35 | 100% | 86% | 50% | 79% |
| 3 | 0.38 | 100% | 86% | 83% | 90% |
| 3 | 0.40 | 100% | 79% | 83% | 87% |
| 3 | 0.42 | 100% | 79% | 83% | 87% |
| 3 | 0.45 | 86% | 79% | 100% | 88% |
| 3 | 0.50 | 57% | 50% | 100% | 69% |

En iyi denge: **K=3, eşik=0.38** (isabet 100%, yazım hatalı 86%, çekimserlik 83%)

