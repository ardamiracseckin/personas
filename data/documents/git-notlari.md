# Git Notları

## Temel durum ve geçmiş

Hangi dosyaların değiştiğini, hangilerinin sahnelendiğini (staged) görmek için `git status` çalıştırılır. Kısa çıktı isteniyorsa `git status --short` daha okunaklıdır.

Commit geçmişini tek satırlık özet halinde görmek için `git log --oneline` kullanılır. Son beş commit için `git log --oneline -5`, hangi dosyaların değiştiğini de görmek için `git log --stat` yazılır.

Henüz sahnelenmemiş değişiklikleri görmek için `git diff`, sahnelenmiş olanları görmek için `git diff --staged` kullanılır.

## Değişiklikleri kaydetme

Bir dosyayı sahnelemek için `git add dosya-adi`, tüm değişiklikleri sahnelemek için `git add .` yazılır. Sahnelenen değişiklikler `git commit -m "mesaj"` ile kaydedilir.

Son commit'in mesajını düzeltmek veya unutulan bir dosyayı ona eklemek için `git commit --amend` kullanılır. Bu komut geçmişi değiştirdiği için yalnızca henüz push edilmemiş commit'lerde güvenlidir.

## Geri alma

Son commit'i geri al ama değişiklikleri çalışma alanında koru: `git reset --soft HEAD~1`. Bu, commit'i açar ama dosyalara dokunmaz.

Son commit'i ve değişiklikleri tamamen sil: `git reset --hard HEAD~1`. Bu komut geri alınamaz, dikkatli kullanılmalıdır.

Tek bir dosyadaki kaydedilmemiş değişiklikleri geri almak için `git restore dosya-adi` kullanılır. Sahnelemeyi geri almak için `git restore --staged dosya-adi` yazılır.

Zaten push edilmiş bir commit'i güvenli şekilde geri almak için `git revert commit-hash` kullanılır; bu, geçmişi silmek yerine ters bir commit ekler.

## Stash — geçici saklama

Yarım kalan değişiklikleri geçici olarak saklamak için `git stash` çalıştırılır; çalışma alanı temizlenir. Saklananı geri getirmek için `git stash pop`, listelemek için `git stash list` kullanılır.

Takipsiz (untracked) dosyaların da saklanması isteniyorsa `git stash -u` yazılır.

## Dallar

Yeni bir dal oluşturup ona geçmek için `git checkout -b yeni-dal-adi` veya modern karşılığı `git switch -c yeni-dal-adi` kullanılır.

Var olan bir dala geçmek için `git switch dal-adi`, dalları listelemek için `git branch` yazılır. İşi biten bir dalı silmek için `git branch -d dal-adi` kullanılır.

Bir dalı ana dala birleştirmek için önce hedef dala geçilir, sonra `git merge dal-adi` çalıştırılır.

## Çakışma çözme

Merge sırasında çakışma çıkarsa Git, çakışan dosyalara `<<<<<<<`, `=======` ve `>>>>>>>` işaretlerini koyar. Dosya elle düzeltilip işaretler silinir, ardından `git add dosya-adi` ve `git commit` ile birleştirme tamamlanır.

Birleştirmeden vazgeçmek için `git merge --abort` kullanılır; çalışma alanı birleştirme öncesi haline döner.

## Uzak depo

Yerel commit'leri uzak depoya göndermek için `git push origin dal-adi` kullanılır. Dal uzakta yoksa ilk gönderimde `git push -u origin dal-adi` yazmak, sonraki gönderimlerde sadece `git push` demeyi sağlar.

Uzaktaki değişiklikleri almak için `git pull`, sadece indirip birleştirmemek için `git fetch` kullanılır.

Uzak adresleri görmek için `git remote -v` çalıştırılır.

## .gitignore

Depoya girmemesi gereken dosyalar `.gitignore` dosyasında satır satır belirtilir. Tipik örnekler: `.venv/`, `__pycache__/`, `*.db`, `.DS_Store`.

Bir dosya yanlışlıkla zaten commit edilmişse `.gitignore`'a eklemek yetmez; `git rm --cached dosya-adi` ile takipten çıkarılması gerekir.
