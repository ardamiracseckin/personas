# Değerlendirme sonuçları — 19.08.2026 00:32

| Ayar | Değer |
|---|---|
| Sohbet modeli | `qwen2.5-1.5b` |
| Embedding modeli | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| TOP_K | 2 |
| SIM_THRESHOLD | 0.15 |
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

## Erişim isabeti (hit@2) — 100% (14/14)

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

| K | Eşik | Erişim isabeti | Çekimserlik | Denge |
|---|---|---|---|---|
| 2 | 0.15 | 100% | 0% | 50% |
| 2 | 0.20 | 100% | 0% | 50% |
| 2 | 0.25 | 100% | 33% | 67% |
| 2 | 0.30 | 100% | 33% | 67% |
| 2 | 0.35 | 100% | 50% | 75% |
| 2 | 0.40 | 100% | 83% | 92% |
| 2 | 0.45 | 86% | 100% | 93% |
| 2 | 0.50 | 57% | 100% | 79% |
| 3 | 0.15 | 100% | 0% | 50% |
| 3 | 0.20 | 100% | 0% | 50% |
| 3 | 0.25 | 100% | 33% | 67% |
| 3 | 0.30 | 100% | 33% | 67% |
| 3 | 0.35 | 100% | 50% | 75% |
| 3 | 0.40 | 100% | 83% | 92% |
| 3 | 0.45 | 86% | 100% | 93% |
| 3 | 0.50 | 57% | 100% | 79% |
| 5 | 0.15 | 100% | 0% | 50% |
| 5 | 0.20 | 100% | 0% | 50% |
| 5 | 0.25 | 100% | 33% | 67% |
| 5 | 0.30 | 100% | 33% | 67% |
| 5 | 0.35 | 100% | 50% | 75% |
| 5 | 0.40 | 100% | 83% | 92% |
| 5 | 0.45 | 86% | 100% | 93% |
| 5 | 0.50 | 57% | 100% | 79% |

En iyi denge: **K=2, eşik=0.45** (isabet 86%, çekimserlik 100%)

