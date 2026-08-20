# Değerlendirme sonuçları — 20.08.2026 11:16

| Ayar | Değer |
|---|---|
| Sohbet modeli | `phi-4-mini` |
| Embedding modeli | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| TOP_K | 3 |
| SIM_THRESHOLD | 0.3 |
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
| C01 | Ekran görüntüsünü belirli bir bölgeden nasıl | macos-kisayollar.md | macos-kisayollar.md | 0.651 | ✅ |
| C02 | Git'te son commit'i geri alıp değişiklikleri | git-notlari.md | git-notlari.md | 0.661 | ✅ |
| C03 | Yarım kalan değişiklikleri geçici olarak nas | git-notlari.md | git-notlari.md | 0.423 | ✅ |
| C04 | Klasördeki gizli dosyaları da listeleyen kom | terminal-komutlar.md | terminal-komutlar.md, macos-kisayollar.md, vscode-notlari.md | 0.535 | ✅ |
| C05 | Bir dosyanın içinde metin aramak için hangi  | terminal-komutlar.md | terminal-komutlar.md | 0.500 | ✅ |
| C06 | Python'da sanal ortam nasıl oluşturulur ve e | python-notlari.md | python-notlari.md, vscode-notlari.md | 0.639 | ✅ |
| C07 | requirements.txt içindeki bağımlılıkları nas | python-notlari.md | python-notlari.md, rag-kavramlari.md, sqlite-notlari.md | 0.484 | ✅ |
| C08 | SQLite'ta tablo zaten varsa hata almamak içi | sqlite-notlari.md | sqlite-notlari.md | 0.658 | ✅ |
| C09 | Embedding vektörleri SQLite'ta hangi biçimde | sqlite-notlari.md | sqlite-notlari.md, rag-kavramlari.md | 0.655 | ✅ |
| C10 | Foundry Local'de yüklü bir modeli bellekten  | foundry-local-notlari.md | foundry-local-notlari.md | 0.481 | ✅ |
| C11 | Foundry Local servisinin adresi neden koda g | foundry-local-notlari.md | foundry-local-notlari.md | 0.642 | ✅ |
| C12 | RAG'in üç adımı nedir? | rag-kavramlari.md | rag-kavramlari.md | 0.578 | ✅ |
| C13 | Benzerlik eşiği çok yüksek olursa ne olur? | rag-kavramlari.md | rag-kavramlari.md | 0.626 | ✅ |
| C14 | VS Code'da projenin tamamında nasıl arama ya | vscode-notlari.md | vscode-notlari.md, python-notlari.md | 0.484 | ✅ |

## Yazım hatalı sorularda erişim — 93% (13/14)

| ID | Bozuk yazımlı soru | Beklenen kaynak | En yüksek skor | Sonuç |
|---|---|---|---|---|
| H01 | Ekran görünütsünü belirli bir bölgden nasıl al | macos-kisayollar.md | 0.632 | ✅ |
| H02 | Gitte son commiti geri alıp değişikliklri nası | git-notlari.md | 0.629 | ✅ |
| H03 | Yarım kalan degisiklikleri gecici olarak nasil | git-notlari.md | 0.344 | ✅ |
| H04 | Klasordeki gizli dosyalari da listeleyn komut  | terminal-komutlar.md | 0.488 | ✅ |
| H05 | Bir dosyanin icinde metin aramk icin hangi kom | terminal-komutlar.md | 0.590 | ✅ |
| H06 | Pythonda sanal ortm nasil olusturulur? | python-notlari.md | 0.530 | ✅ |
| H07 | requirements.txt icindeki bagimliliklari nasil | python-notlari.md | 0.463 | ✅ |
| H08 | SQLitede tablo zatn varsa hata almamk icin ne  | sqlite-notlari.md | 0.696 | ✅ |
| H09 | Embeding vektorleri SQLitede hangi bicimde sak | sqlite-notlari.md | 0.675 | ✅ |
| H10 | Foundry Localde yuklu bir modeli bellekten nas | foundry-local-notlari.md | 0.478 | ✅ |
| H11 | Foundry Local servisinin adrsi neden koda gomu | foundry-local-notlari.md | 0.562 | ✅ |
| H12 | RAGin uc adimi nedir? | rag-kavramlari.md | 0.258 | ❌ |
| H13 | Benzerlik esigi cok yuksek olursa ne olur? | rag-kavramlari.md | 0.619 | ✅ |
| H14 | VS Codeda projenin tamaminda nasil arama yapar | vscode-notlari.md | 0.488 | ✅ |

## Çekimserlik (cevaplanamaz sorular) — 83% (5/6)

| ID | Soru | En yüksek skor | Eşiğin altında mı |
|---|---|---|---|
| B01 | Docker imajı nasıl oluşturulur? | 0.274 | ✅ |
| B02 | Kubernetes'te bir pod nasıl silinir? | 0.232 | ✅ |
| B03 | React'te useEffect kancası ne işe yarar? | 0.256 | ✅ |
| B04 | Excel'de düşeyara formülü nasıl yazılır? | 0.285 | ✅ |
| B05 | Ev kredisi faiz oranları nedir? | 0.217 | ✅ |
| B06 | Fotoğrafta diyafram değeri neyi etkiler? | 0.330 | ❌ |

## Eşik / K taraması

| K | Eşik | İsabet | Yazım hatalı isabet | Çekimserlik | Denge |
|---|---|---|---|---|---|
| 3 | 0.30 | 100% | 93% | 83% | 92% |
| 3 | 0.32 | 100% | 93% | 83% | 92% |
| 3 | 0.34 | 100% | 93% | 100% | 98% |
| 3 | 0.35 | 100% | 86% | 100% | 95% |
| 3 | 0.36 | 100% | 86% | 100% | 95% |
| 3 | 0.38 | 100% | 86% | 100% | 95% |
| 3 | 0.40 | 100% | 86% | 100% | 95% |

En iyi denge: **K=3, eşik=0.34** (isabet 100%, yazım hatalı 93%, çekimserlik 100%)

