# Foundry Local Notları

## Foundry Local nedir

Foundry Local, Microsoft'un büyük dil modellerini tamamen kullanıcının cihazında çalıştırmayı sağlayan yerel çalışma zamanı ve SDK'sıdır. Bulut hesabı, abonelik veya internet bağlantısı gerektirmez.

Modelleri kendi kataloğundan indirir, cihazdaki donanıma (CPU, GPU veya NPU) göre en uygun sürümü seçer ve yerel bir HTTP servisi üzerinden sunar. Böylece veri cihazdan hiç çıkmadan çıkarım yapılabilir.

Azure AI Foundry'den farkı şudur: Azure AI Foundry bulutta çalışır, Foundry Local ise aynı model ailelerini yerelde çalıştırır. Bu projede yalnızca yerel sürüm kullanılır.

## Kurulum

macOS'te Homebrew ile kurulur: `brew install microsoft/foundrylocal/foundrylocal`. Kurulumdan sonra `foundry --version` komutu sürümü yazdırır.

Python tarafında resmi paket `pip install foundry-local-sdk` ile kurulur. Servis OpenAI uyumlu bir API sunduğu için standart `openai` istemcisi de kullanılabilir.

## Model yönetimi

Katalogdaki modelleri listelemek için `foundry model list` çalıştırılır. Çıktıda takma ad (alias), cihaz, görev tipi, dosya boyutu ve lisans sütunları bulunur.

Bir modeli indirmek için `foundry model download model-adi`, belleğe yüklemek için `foundry model load model-adi` kullanılır. Yükleme komutu servis kapalıysa servisi de başlatır.

Belleği boşaltmak için `foundry model unload model-adi` çalıştırılır. 8 GB bellekli bir makinede aynı anda tek bir model yüklü tutulmalı, model karşılaştırması yaparken önceki model mutlaka boşaltılmalıdır.

Servisin durumunu ve dinlediği adresi görmek için `foundry service status` kullanılır.

## Yerel API'ye bağlanma

Foundry Local servisi sabit bir port kullanmaz; her başlatmada dinamik bir yerel port seçer. Bu yüzden adres koda gömülmemeli, `foundry service status` çıktısından okunmalı veya SDK'nın verdiği uç nokta kullanılmalıdır.

Servis OpenAI uyumludur: `openai` istemcisi `base_url` olarak `http://127.0.0.1:<port>/v1` adresiyle kurulur. API anahtarı gerekmez, istemci zorunlu tuttuğu için yer tutucu bir değer verilir.

Yüklü model kimliklerini görmek için istemcinin `models.list()` çağrısı kullanılır. Dönen kimlikler takma adın tam sürümüdür, örneğin `qwen2.5-1.5b-instruct-generic-gpu`.

Sohbet isteği standart `chat.completions.create` çağrısıyla yapılır; `system` ve `user` rolleri OpenAI API'sindeki gibi çalışır.

## Model seçimi

Küçük modeller (0.5–2 GB) hızlı yanıt verir ama karmaşık akıl yürütmede zayıftır. Büyük modeller daha iyi cevap üretir ama belleğe sığmayabilir ve yanıt süresi uzar.

Sınırlı bellekte RAG uygulaması için 1–4 GB aralığındaki sohbet modelleri iyi bir dengedir; bağlam zaten belgelerden geldiği için modelin genel bilgisinden çok talimatı izleme becerisi önemlidir.

Katalogda `chat` görevi olan modeller sohbet için kullanılır. Katalogda embedding görevine sahip bir model bulunmuyorsa embedding'ler ayrı bir yerel kütüphaneyle üretilmelidir.

## Sık karşılaşılan sorunlar

"Servise ulaşılamadı" hatası genellikle servisin kapalı olmasından kaynaklanır; `foundry model load model-adi` komutu servisi başlatır.

İlk çağrı yavaştır çünkü model belleğe yükleniyordur. Ölçüm yaparken önce bir ısınma isteği gönderilmeli, süreler ondan sonra kaydedilmelidir.

Model indirme adımı internet gerektirir; indirdikten sonra çalışma tamamen çevrimdışıdır.
