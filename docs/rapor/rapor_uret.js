/**
 * personas proje raporunu (.docx) üretir.
 *
 *   node docs/rapor/rapor_uret.js
 *
 * Ölçüm sayıları docs/eval/degerlendirme-raporu.md ile aynı koşumlardan gelir;
 * rapor güncellenecekse önce değerlendirme koşumu tekrarlanmalıdır.
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  PageBreak, LevelFormat, TableOfContents, Footer, PageNumber,
} = require("docx");

const ACCENT = "8A6D1F";
const GRAY = "595959";
const TABLE_W = 9360; // 6.5" = 9360 DXA

const p = (text, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, line: 276 },
  alignment: opts.align,
  children: [new TextRun({ text, size: opts.size ?? 22, color: opts.color, italics: opts.italics, bold: opts.bold })],
});

const rich = (runs, opts = {}) => new Paragraph({
  spacing: { after: opts.after ?? 120, line: 276 },
  children: runs.map(r => new TextRun({
    text: r.t, bold: r.b, italics: r.i, size: r.size ?? 22,
    font: r.code ? "Consolas" : undefined, color: r.code ? "1F5C3A" : r.color,
  })),
});

const h1 = (text) => new Paragraph({
  text, heading: HeadingLevel.HEADING_1, spacing: { before: 320, after: 160 },
});
const h2 = (text) => new Paragraph({
  text, heading: HeadingLevel.HEADING_2, spacing: { before: 240, after: 120 },
});

const bullet = (text, level = 0) => new Paragraph({
  numbering: { reference: "madde", level },
  spacing: { after: 80, line: 276 },
  children: [new TextRun({ text, size: 22 })],
});

function table(headers, rows, widths) {
  const cols = widths || headers.map(() => Math.floor(TABLE_W / headers.length));
  const cell = (text, { bold, shade, width }) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: shade ? { type: ShadingType.CLEAR, fill: shade, color: "auto" } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { after: 0, line: 240 },
      children: [new TextRun({ text: String(text), bold, size: 20 })],
    })],
  });
  return new Table({
    columnWidths: cols,
    width: { size: TABLE_W, type: WidthType.DXA },
    rows: [
      new TableRow({
        tableHeader: true,
        children: headers.map((htxt, i) => cell(htxt, { bold: true, shade: "EFE8D6", width: cols[i] })),
      }),
      ...rows.map((r, ri) => new TableRow({
        children: r.map((c, i) => cell(c, { width: cols[i], shade: ri % 2 ? "F7F7F7" : undefined })),
      })),
    ],
  });
}

const spacer = () => new Paragraph({ spacing: { after: 160 }, children: [] });

// ---------------------------------------------------------------- içerik

const kapak = [
  new Paragraph({ spacing: { before: 2400, after: 0 }, children: [
    new TextRun({ text: "PROJE RAPORU", size: 20, color: ACCENT, bold: true, characterSpacing: 60 })] }),
  new Paragraph({ spacing: { before: 200, after: 0 }, children: [
    new TextRun({ text: "personas", size: 72, bold: true })] }),
  new Paragraph({ spacing: { before: 80, after: 400 }, children: [
    new TextRun({ text: "Microsoft Foundry Local ile çevrimdışı çalışan yerel RAG asistanı", size: 30, color: GRAY })] }),
  new Paragraph({ border: { top: { style: BorderStyle.SINGLE, size: 6, color: ACCENT } }, spacing: { after: 240 }, children: [] }),
  rich([{ t: "Program: ", b: true }, { t: "Summer School — One-Month Project Plan: Local RAG AI Assistant with Microsoft Foundry Local" }]),
  rich([{ t: "Faz: ", b: true }, { t: "3 — Test, değerlendirme ve dokümantasyon" }]),
  rich([{ t: "Donanım: ", b: true }, { t: "Apple M2, 8 GB RAM, macOS 26.5.1" }]),
  rich([{ t: "Tarih: ", b: true }, { t: "19 Ağustos 2026" }]),
  new Paragraph({ children: [new PageBreak()] }),
];

const icindekiler = [
  h1("İçindekiler"),
  new TableOfContents("İçindekiler", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

const govde = [
  h1("1. Amaç ve senaryo"),
  p("personas, kullanıcının kendi belgelerinden kaynak göstererek cevap veren, tamamen çevrimdışı çalışan bir kişisel asistandır. Asistanın dil modeli Microsoft Foundry Local ile kullanıcının cihazında koşar; hiçbir soru, belge veya kişisel veri buluta gönderilmez."),
  p("Senaryo şudur: kullanıcı kendi teknik notlarını (git, terminal, Python, SQLite, macOS, VS Code, Foundry Local, RAG kavramları) bir klasörde tutar. Bir şeyi hatırlamak istediğinde asistana Türkçe sorar; asistan ilgili not parçasını bulur, cevabı yalnızca o parçaya dayanarak yazar ve hangi belgeden yararlandığını söyler. Notlarında olmayan bir şey sorulduğunda uydurmaz, bilmediğini söyler."),
  p("Staj planındaki çekirdek teslim budur. Bunun üzerine, asistanı tek işlevli bir soru-cevap kutusundan araç kullanabilen bir yardımcıya dönüştüren üç yetenek eklenmiştir: Apple Takvim okuma ve onaylı etkinlik ekleme, Apple Mail okuma ve onaylı e-posta gönderme, macOS uygulamalarını adıyla açma."),

  h1("2. Microsoft plan gereksinimleri ile eşleme"),
  p("Aşağıdaki tablo, program planında istenen her bileşenin bu projede nasıl karşılandığını gösterir."),
  table(
    ["Plandaki gereksinim", "Bu projedeki karşılığı"],
    [
      ["Foundry Local ile cihaz üstü çıkarım, sıfır ağ çağrısı", "app/llm.py — servisin dinamik yerel portu keşfedilip OpenAI uyumlu istemciyle konuşulur"],
      ["RAG deseni: retrieve, augment, generate", "retriever.get_top_chunks() → assistant.answer() bağlamı isteme ekler → llm.chat() cevabı üretir"],
      ["Embedding + kosinüs benzerliği ile anlamsal arama", "fastembed ile yerel embedding, app/similarity.py içinde kosinüs, bellek içi sıralama"],
      ["SQLite'ta belge parçaları ve vektörler", "app/store.py — chunks(id, source, text, embedding) tablosu, vektör JSON metni olarak"],
      ["5–10 belge, 1–3 paragraflık parçalar", "8 Türkçe teknik not, 58 parça, ortalama 433 karakter"],
      ["İstem tasarımı: bağlam dışına çıkma, kaynak göster, bilmiyorsan söyle", "assistant.SYSTEM_PROMPT — üç kural açık biçimde yazılı"],
      ["Arayüz (CLI asgari, Streamlit veya HTML+JS)", "Planın C seçeneği: FastAPI + tek sayfa arayüz (server/), ayrıca ui/cli.py"],
      ["Test seti: cevaplanabilir, cevaplanamaz ve uç durum soruları", "eval/questions.json — 50 soru, altı kategori (yazım hatalı ve kısa sorgular dâhil)"],
      ["Yanıt süresi ~1–3 saniye", "Kısmen: p50 3,0 sn, p95 6,7 sn (üretim sınırı ayarlandıktan sonra; öncesinde p95 48 sn idi)"],
      ["Proje raporu ve final sunumu", "Bu rapor ve docs/sunum/index.html"],
    ],
    [3400, 5960],
  ),

  h1("3. Mimari"),
  p("Sistem tek makinede çalışır ve katmanlıdır; her modülün tek sorumluluğu vardır."),
  rich([{ t: "Soru → router → (belge erişimi | takvim | mail | uygulama) → Foundry Local → cevap + kaynak", code: true }], { after: 200 }),
  h2("3.1 Yönlendirme"),
  p("router.route() gelen soruyu dört araçtan birine ve bir niyete (okuma / yazma / açma) eşler. Katman kural tabanlıdır: anahtar kelimeler aracı, fiiller niyeti belirler. Hiçbir kural eşleşmezse varsayılan belge aramasıdır. Küçük bir modelin araç seçiminde şaşırma riski böylece tamamen ortadan kalkar; ölçümde yönlendirme doğruluğu 6/6 çıkmıştır."),
  h2("3.2 Belge akışı"),
  p("Soru embedding'e çevrilir, veritabanındaki 58 parçanın vektörleriyle kosinüs benzerliği hesaplanır ve buna yazım hatalarına dayanıklı sözlüksel bir skor eklenir (0,75 kosinüs + 0,25 sözlüksel); eşiği geçen en iyi üç parça bağlam olarak isteme eklenir. Eşiği geçen parça yoksa dil modeli hiç çağrılmaz; asistan doğrudan bilgisi olmadığını söyler. Bu, hem doğruluk hem hız açısından belirleyicidir: cevaplanamaz sorular ortalama 0,02 saniyede yanıtlanır."),
  h2("3.3 Cevap akışı ve çok turlu konuşma"),
  p("Cevap, modelden geldikçe parça parça arayüze yazılır (assistant.answer_stream). Ölçülen süre değişmez ama kullanıcı ilk kelimeleri saniyenin altında görür; küçük modelde p95 gecikmenin on saniyeyi aşabildiği düşünülürse bu belirgin bir fark yaratır. Model çağrılmayan akışlarda (yazma taslağı, bilgi bulunamaması, uygulama açma) tek seferde sonuç döner."),
  p("Asistan son iki turu hatırlar: geçmiş isteme eklenir ve işaret zamiri içeren takip soruları erişim için önceki soruyla genişletilir. Genişletme uzunluğa değil zamire bakar; böylece kendi başına anlamlı kısa sorular (\"RAG nedir?\") bozulmaz. Örnek: \"Python'da sanal ortam nasıl oluşturulur?\" sorusunun ardından \"Peki onu nasıl kapatırım?\" sorusu doğru biçimde deactivate cevabını verir."),

  h2("3.4 Yazma işlemleri ve onay kapısı"),
  p("Takvime etkinlik eklemek ve e-posta göndermek yazma işlemleridir ve mimaride ayrı tutulur. assistant.answer() yazma niyeti gördüğünde işlemi yapmaz; taslağı pending_action olarak döndürür. Arayüz taslağı kullanıcıya gösterir ve onay ister; işlemi yalnızca onay sonrası çağrılan assistant.confirm() gerçekleştirir. Silme yeteneği hiç uygulanmamıştır."),

  h2("3.5 Arayüz"),
  p("Arayüz, FastAPI üzerinde çalışan tek sayfalık bir web uygulamasıdır (server/). Cevaplar SSE ile token token akıtılır; sohbetler SQLite'ta kalıcıdır; markdown ve kod blokları biçimlendirilir; kaynak rozetine tıklandığında cevabın dayandığı parça metni açılır; her cümlenin sonunda dayandığı parçanın numarası satır içi atıf olarak görünür; belgeler sürükle-bırak ile bilgi tabanına eklenir (.md, .txt ve .pdf) ve model arayüzden değiştirilebilir."),
  p("Arayüz hiçbir dış kaynağa bağlanmaz: ikon fontu, betik kütüphanesi veya yazı tipi CDN'i yoktur. Bu bilinçli bir kısıttır, çünkü projenin temel iddiası tamamen çevrimdışı çalışmaktır. Program planındaki üç arayüz seçeneğinden C seçeneğine (yerel sunucu + HTML/JS) karşılık gelir."),

  h1("4. Teknoloji seçimleri ve sapmaların gerekçesi"),
  table(
    ["Katman", "Seçim", "Gerekçe"],
    [
      ["Sohbet modeli", "phi-4-mini (Foundry Local)", "Dört aday arasında cevap doğruluğu açık ara en yüksek model; gecikme ve bellek bedeli bilinçli kabul edildi (Bölüm 6.4)"],
      ["Embedding", "paraphrase-multilingual-MiniLM-L12-v2 (fastembed)", "Foundry Local kataloğunda embedding görevine sahip model yok; çok dilli ve Türkçeye uygun"],
      ["Veritabanı", "SQLite", "Sunucusuz, tek dosya, Python ile birlikte gelir"],
      ["Benzerlik araması", "Bellek içi kosinüs", "58 parça için kaba kuvvet arama milisaniyeler sürer; vektör veritabanı gereksiz karmaşıklık olurdu"],
      ["Arayüz", "CLI + tek sayfa web arayüzü", "CLI hata ayıklama ve ölçüm için. Streamlit denendi ve bırakıldı: dış bağımlılık getiriyor ve akış/kaynak paneli üzerinde yeterli denetim vermiyordu. Yerine bağımlılıksız FastAPI + SSE arayüzü (planın C seçeneği)"],
      ["Takvim / Mail", "AppleScript", "macOS uygulamalarına yerel erişim; ağ veya API anahtarı gerektirmez"],
    ],
    [1700, 3200, 4460],
  ),
  spacer(),
  h2("4.1 Embedding neden Foundry Local'de değil"),
  p("Program planı embedding'lerin de Foundry Local üzerinden üretilmesini öngörür. Ancak katalogda embedding görevine sahip bir model bulunmamaktadır; kontrol bu raporun hazırlandığı gün tekrarlanmış ve katalogdaki modellerin tamamının chat, tools veya vision-language-chat görevine sahip olduğu görülmüştür. Bu nedenle vektörler fastembed ile, yine tamamen yerel ve çevrimdışı biçimde üretilmektedir. Projenin temel taahhüdü olan \"hiçbir ağ çağrısı yok\" ilkesi bozulmamıştır."),
  h2("4.2 Kapsam genişletmesi"),
  p("Takvim, mail ve uygulama açma yetenekleri planın çekirdek kapsamında yoktur; bilinçli bir genişletmedir. Çekirdek RAG teslimini bozmamak için bu yetenekler ayrı araç modülleri olarak eklenmiş, router'a birer dal olarak bağlanmıştır. Yazma işlemleri insan onayına bağlandığı için asistan hiçbir koşulda kullanıcının haberi olmadan e-posta göndermez veya takvimi değiştirmez."),

  h1("5. Kurulum ve kullanım"),
  p("Aşağıdaki adımlar temiz bir macOS makinesinde projeyi çalışır hâle getirir. Yalnızca model indirme adımı internet gerektirir; sonrasında sistem tamamen çevrimdışı çalışır."),
  bullet("Foundry Local kurulumu: brew install microsoft/foundrylocal/foundrylocal"),
  bullet("Sohbet modelinin indirilmesi ve yüklenmesi: foundry model download phi-4-mini, ardından foundry model load phi-4-mini"),
  bullet("Python ortamı: python3 -m venv .venv, source .venv/bin/activate, pip install -r requirements.txt"),
  bullet("Belgelerin işlenmesi: python -m app.ingest (58 parça veritabanına yazılır)"),
  bullet("Ortam doğrulaması: python scripts/setup_check.py (dört kontrol de PASS vermeli)"),
  bullet("Kullanım: python -m ui.cli veya streamlit run ui/web.py"),
  spacer(),
  p("Takvim ve mail yeteneklerinin ilk kullanımında macOS otomasyon izni ister: Sistem Ayarları > Gizlilik ve Güvenlik > Otomasyon bölümünden Terminal'e Mail ve Takvim erişimi verilmelidir."),

  h1("6. Değerlendirme sonuçları"),
  p("Ölçümler 50 soruluk sabit bir set (eval/questions.json) üzerinde, scripts/evaluate.py ile yapılmıştır. Setin 24 sorusu dil modelini çağırır; kalan 26 soru (yönlendirme, yazım hatalı ve kısa sorgular) model çalıştırılmadan ölçülür. Gecikmeler koşumdan koşuma değiştiği için (aynı model iki koşumda p50 3,95 ve 4,72 saniye vermiştir) tek bir ondalık basamağa anlam yüklenmemelidir; modeller arası fark bu oynaklıktan büyüktür. Ham koşum çıktıları docs/eval/ klasöründedir. Ayrıntılı analiz için docs/eval/degerlendirme-raporu.md dosyasına bakılabilir."),
  h2("6.1 Soru seti"),
  table(
    ["Kategori", "Adet", "Beklenen davranış"],
    [
      ["cevaplanabilir", "14", "Belgelerden doğru cevap ve doğru kaynak"],
      ["cevaplanamaz", "6", "Bilmediğini söylemeli, uydurmamalı"],
      ["uc_durum", "4", "Boş sorgu, tek kelime, çok genel ve çok uzun soru; çökmemeli"],
      ["yonlendirme", "6", "Doğru araca ve doğru niyete gitmeli"],
    ],
    [2200, 1000, 6160],
  ),
  spacer(),
  h2("6.2 Bilgi tabanı ve parçalama"),
  p("Faz 3 başlangıcında bilgi tabanı 3 belge ve toplam 3 parçadan ibaretti: belgeler parça sınırının çok altında kaldığı için parçalama hiç devreye girmiyordu. Belge seti 8 nota çıkarılmış, parçalama başlık farkındalıklı hâle getirilmiştir; artık markdown başlıkları parça sınırı sayılır ve her parça kendi başlığını taşır. Sonuç 58 parça, ortalama 433 karakterdir. 800 ve 1000 karakter sınırlarının aynı sonucu vermesi, parçaların karakter sınırıyla değil belgelerin kendi bölüm yapısıyla bölündüğünü gösterir."),
  h2("6.3 Erişim eşiği"),
  p("Başlangıçtaki SIM_THRESHOLD = 0,20 ve TOP_K = 3 değerleri ölçüme değil tahmine dayanıyordu. Tarama, 0,20 eşiğinde cevaplanamaz soruların altısının da eşiği geçtiğini, yani alakasız bağlamın modele gönderildiğini ortaya çıkardı: uydurmama garantisi tamamen modelin insafındaydı."),
  table(
    ["Eşik", "Erişim isabeti", "Çekimserlik", "Denge"],
    [
      ["0,20 (eski)", "%100", "%0", "%50"],
      ["0,30", "%100", "%33", "%67"],
      ["0,35", "%100", "%50", "%75"],
      ["0,40 (seçilen)", "%100", "%83", "%92"],
      ["0,45", "%86", "%100", "%93"],
      ["0,50", "%57", "%100", "%79"],
    ],
    [2340, 2340, 2340, 2340],
  ),
  spacer(),
  p("Cevaplanabilir soruların en düşük benzerlik skoru 0,430; cevaplanamazların en yükseği 0,440'tır. İki dağılım çakıştığı için kusursuz ayıran bir eşik yoktur. 0,40 seçilmiştir: erişim isabetini tam tutar, çekimserliği sıfırdan 5/6'ya çıkarır, kalan tek sızıntıyı istemdeki kural karşılar. TOP_K değeri 3'te bırakılmıştır; K=1 iken isabet 13/14'e düşmekte, K=2 ve üzeri 14/14 vermektedir."),
  h2("6.4 Model karşılaştırması"),
  p("Aynı soru seti, 8 GB belleğe sığan dört sohbet modeliyle koşulmuştur. Her koşumdan önce bir önceki model bellekten boşaltılmış ve ısınma turu yapılmıştır."),
  "__MODEL_TABLE__",
  spacer(),
  "__MODEL_NOTES__",
  h2("6.5 Nihai sonuçlar"),
  table(
    ["Metrik", "Sonuç"],
    [
      ["Yönlendirme doğruluğu", "6/6 (%100)"],
      ["Erişim isabeti hit@3", "14/14 (%100)"],
      ["Yazım hatalı sorularda erişim", "14/14 (%100)"],
      ["Kısa / anahtar kelime sorgularında erişim", "6/6 (%100)"],
      ["Otomatik kalite puanı", "28/28 (%100)"],
      ["Sadakat (ortalama)", "%80 — 16 cevapta ölçüldü"],
      ["Kod sadakati", "10/10 cevapta uydurulmuş komut yok"],
      ["Cevaplanamazda çekimserlik", "6/6 (%100)"],
      ["Ortalama yanıt süresi", "3,32 sn"],
      ["p50 / p95 yanıt süresi", "3,03 sn / 6,65 sn"],
      ["Uç durumlarda çökme", "0"],
      ["Birim, HTTP ve regresyon testleri", "270 test, tamamı geçiyor"],
    ],
    [4680, 4680],
  ),
  spacer(),
  p("Çekimserlik iki katmanda çalışır ve ölçüm, birinci katmanın belirleyici olduğunu göstermiştir. Cevaplanamaz altı sorunun altısında da benzerlik eşiği hiç parça bırakmamış, asistan dil modelini hiç çağırmadan ortalama 0,02 saniyede bilgisi olmadığını söylemiştir."),
  p("Ölçümün önceki turlarında eşiği aşan tek soru vardı (\"Fotoğrafta diyafram değeri neyi etkiler?\") ve modeller o soruda ayrışmıştı: phi-4-mini bağlamdaki alakasız macOS parçasını kullanmamış, ancak istemdeki \"yalnızca bağlamı kullan\" kuralını da çiğneyerek kendi genel bilgisinden doğru bir fotoğrafçılık cevabı vermişti. Aynı soruda qwen2.5-1.5b çekimser kalmıştı. Erişime sözlüksel katman eklendikten sonra bu soru da eşiğin altında kalmış ve çekimserlik 6/6 olmuştur. Bulgu yine de seçilen modelin bilinen ödünüdür: daha güçlü model, bağlam dışına çıkma eğilimini de beraberinde getirmektedir. Bu eğilimin ne sıklıkta gerçekleştiği artık varsayıma bırakılmamakta, Bölüm 7'de ölçülmektedir."),

  h1("7. Sadakat: cevap getirilen parçaya mı dayanıyor"),
  p("Bölüm 6'daki otomatik kalite puanı \"doğru bilgi cevapta geçiyor mu\" sorusunu yanıtlar. Bu, RAG'in asıl iddiasını sınamaz: model doğru cevabı kendi ezberinden de verebilir ve o durumda erişim zinciri fiilen çalışmamış olur. Değerlendirmeye bu yüzden ikinci bir ölçüt eklenmiştir."),
  h2("7.1 Ölçüt"),
  p("app/grounding.py, cevaptaki içerik sözcüklerinin kaçının getirilen parçalarda (yaklaşık olarak) geçtiğini hesaplar. Dil modeli gerektirmez, koşum süresine eklenmez. İki eleme yapılır: sorudan gelen sözcükler sayılmaz, yoksa soruyu tekrarlayan cevap haksız yere yüksek puan alır; modelin kendi cümle kurma sözcükleri de sayılmaz. İkincisi ölçütün ilk koşumundan sonra eklenmiştir."),
  p("İlk koşum ölçütün kendi kusurunu göstermiştir. \"`ls -la` komutunu kullanın.\" cevabı 0,50 almıştı: komut bağlamdan geliyor, ancak \"komutunu\" ve \"kullanın\" bağlamda geçmiyordu. Türkçe çekim ekleri nedeniyle tam sözcük yerine gövde başlangıcı eşleştirilerek bu sözcükler elendi ve ortalama sadakat %67'den %80'e çıktı. Değişen model ya da cevap değil, ölçütün gürültüsüydü. Bir metriğe karar verdirmeden önce onun neyi cezalandırdığı incelenmelidir."),
  p("Sözlüksel oran bulanık bir ölçüttür; komut uydurmak ise ikili bir hatadır ve kullanıcının çalıştıracağı yanlış komut demektir. Bu nedenle ayrıca kod sadakati ölçülür: cevapta ters tırnak içinde geçen her ifade bağlamda birebir bulunmalıdır."),
  h2("7.2 Sonuçlar"),
  table(
    ["Ölçüt", "Sonuç"],
    [
      ["Sadakat (ortalama)", "%80 — belge akışıyla üretilmiş 16 cevapta ölçüldü"],
      ["Kod sadakati", "10/10 cevapta bağlamda olmayan komut yok"],
      ["Eşiğin (0,60) altında kalan", "2 cevap, ikisi de uç durum kategorisinden"],
    ],
    [4680, 4680],
  ),
  spacer(),
  p("Eşiğin altında kalan iki cevap, tek sözcüklük \"git\" sorgusu (0,17) ile \"hem git hem python hem sqlite kullanıyorum, nereden başlayayım\" sorusudur (0,31). İkisinde de model belgeye değil kendi bilgisine dayanarak genel tavsiye vermektedir; ölçüt tam olarak yakalaması gerekeni yakalamaktadır. Bölüm 6'daki %100'lük kalite puanının arkasında kalan tek gerçek boşluk buydu."),
  h2("7.3 Satır içi atıflar"),
  p("Arayüzde her cümlenin sonunda dayandığı parçanın numarası görünür; tıklandığında ilgili parça açılıp vurgulanır. İki yol vardı. Birincisi isteme \"her cümleye kaynak numarası yaz\" kuralı eklemekti; bunun bedeli daha uzun istem, daha fazla çıktı belirteci ve daha yüksek gecikmedir. Üretim sınırının geniş bırakılmasının p95 gecikmeyi 48 saniyeye çıkardığı bu projede ölçülmüştür. Ayrıca bu boyuttaki bir model numaraları karıştırır ve istem değiştiği için tüm kalite ve çekimserlik ölçümü geçersiz olurdu."),
  p("İkinci yol, atıfı cevap üretildikten sonra çıkarmaktır: app/citations.py her cümleyi, sadakat ölçümünün kullandığı sözlüksel eşleştirmeyle en çok örtüşen parçaya bağlar. Bu yol seçilmiştir. Ölçülen maliyet cevap başına 2,7 milisaniyedir; istem, cevaplar ve Bölüm 6'daki metriklerin hiçbiri değişmemiştir. Atıflar veritabanına yazılmaz, metin ve parçalar zaten saklandığı için geçmiş sohbet açıldığında yeniden hesaplanır."),
  p("Bedeli açıkça belirtmek gerekir: atıf, modelin beyanı değil ölçüme dayalı bir tahmindir. Eşiği geçemeyen cümle atıfsız bırakılır, çünkü yanlış atıf atıfsızlıktan kötüdür."),
  h2("7.4 İki eşiğin ölçümle seçilmesi"),
  p("Bölüm 6.3'te erişim eşiği tahminle değil taramayla seçilmişti. Aynı kural bu bölümün eşiklerine de uygulanmıştır. Sadakat eşiği için ayrım iki grup üzerinden yapılır: cevaplanabilir sorular belgeye dayanmak zorundadır, uç durum cevaplarında ise model kendi bilgisine dayanır."),
  table(
    ["Sadakat eşiği", "Yanlış alarm", "Yakalanan uç durum"],
    [
      ["0,40 – 0,60", "0/13", "2/3"],
      ["0,65 – 0,70", "2/13", "3/3"],
      ["0,80", "3/13", "3/3"],
    ],
    [3120, 3120, 3120],
  ),
  spacer(),
  p("0,60 seçilmiştir: yanlış alarm vermeyen en yüksek değer. 0,65'e çıkmak üçüncü uç durumu yakalamakta, ancak bedeli iki doğru cevabı dayanaksız göstermektir; dayanaksızlık iddiası yanlış çıktığında ölçüt güvenilirliğini yitirir."),
  p("Atıf eşiği için ilk denenen ölçüt, atıfın sorunun beklenen kaynağı dışına gitmesiydi. Bu ölçüt hiçbir eşikte ayırt etmedi: erişim isabeti %100 olduğu için ilk parça neredeyse her zaman beklenen kaynaktır. Ölçüt değiştirilmiş, yerine gerçek denge ölçülmüştür: cevaplanabilir sorularda kapsama yüksek olmalı, uç durum cevaplarında model doğaçladığı için atıf verilmemelidir."),
  table(
    ["Atıf eşiği", "Kapsama (cevaplanabilir)", "Doğaçlamaya atıf (uç durum)"],
    [
      ["0,40", "23/23 (%100)", "10/26"],
      ["0,50", "21/23 (%91)", "7/26"],
      ["0,55 (seçilen)", "21/23 (%91)", "6/26"],
      ["0,70", "18/23 (%78)", "6/26"],
      ["0,80", "15/23 (%65)", "6/26"],
    ],
    [3120, 3120, 3120],
  ),
  spacer(),
  p("0,55 eğrinin dirseğidir. 0,40'a inmek kapsamayı iki cümle artırırken doğaçlama cümlelerine verilen atıfı 6'dan 10'a çıkarmakta; 0,70'e çıkmak ise kapsamayı %78'e düşürmekte, karşılığında doğaçlamaya atıfı hiç azaltmamaktadır. Tarama, kayıtlı bir koşum üzerinden dil modeli çağrılmadan tekrarlanabilir: python scripts/evaluate.py --sadakat-tarama <koşum.json>"),
  spacer(),

  h1("8. Sınırlar"),
  bullet("Küçük yerel model genel sohbette ve akıl yürütmede zayıftır; sistem en iyi kendi belgelerinden cevap verirken çalışır."),
  bullet("Takvim ve mail entegrasyonu yalnızca Apple uygulamalarıyla ve yalnızca macOS'te çalışır."),
  bullet("Bellek içi kosinüs araması binlerce parçaya kadar yeterlidir; daha büyük veri kümelerinde vektör indeksi gerekir."),
  bullet("Otomatik kalite puanı beklenen ifadelerin cevapta geçip geçmediğine bakar; anlamca doğru ama farklı sözcüklerle yazılmış bir cevabı düşük puanlayabilir."),
  bullet("Yönlendirme kural tabanlıdır; tasarım dokümanında öngörülen model tabanlı üçüncü katman, kural katmanı ölçümde 6/6 verdiği için uygulanmamıştır."),
  bullet("Sadakat ölçütü sözlükseldir: aynı bilgiyi bambaşka sözcüklerle yeniden yazan bir cevabı düşük puanlar. Aynı sebeple satır içi atıflar modelin beyanı değil, ölçüme dayalı bir tahmindir."),
  bullet("Görsel yükleme kapalıdır: Foundry Local'in yerel uç noktası içerik dizisini düz metne indirgeyip görseli modele iletmemektedir (kod tarafı hazırdır)."),

  h1("9. Öğrenilenler"),
  p("Makul görünen bir ayar sessizce bozuk olabilir. 0,20 benzerlik eşiği hiçbir hata vermeden çalışıyordu; sistemin uydurmaya karşı korumasını tamamen devre dışı bıraktığı ancak cevaplanamaz sorular ölçüme sokulunca görüldü. Ayar seçmek bir tahmin işi değil, ölçüm işidir."),
  p("Bilgi tabanı büyümeden RAG sınanamaz. Üç kısa belgeyle sistem çalışıyor görünüyordu; oysa erişim katmanı fiilen devre dışıydı. Parça sayısı gerçekçi bir seviyeye çıkarılmadan ne erişim isabeti ne de çekimserlik anlamlı biçimde ölçülebilir."),
  p("Savunma tek katmanda olmaz. Eşik tek başına 5/6, istem kuralı tek başına belirsiz sonuç verirken ikisi birlikte 6/6 vermektedir. Aynı hedefi farklı mekanizmalarla iki kez korumak, küçük modellerle çalışırken pahalı değil zorunludur."),
  p("Büyük model her zaman iyi model değildir. 2,2 GB'lık phi-3.5-mini, 1,5 GB'lık qwen2.5-1.5b'ye karşı hem daha yavaş hem daha hatalıdır. Sınırlı donanımda seçim ölçütü parametre sayısı değil, hedef dilde talimat takibi ve gecikmedir."),

  p("Sessiz hata, gürültülü hatadan tehlikelidir. Ölçümler bittikten sonra yapılan kod incelemesi üç hata çıkardı: yönlendirmede takvim kelimelerinin mail isteğini bastırması, tanınmayan tarih ifadelerinin sessizce bugüne düşmesi ve web arayüzünün ikon fontunu internetten çekmesi. Üçü de istisna fırlatmıyor, test kırmıyor, yalnızca yanlış davranıyordu. Soru seti de bunları yakalamamıştı çünkü sorular çakışmayacak biçimde seçilmişti; bir test kümesinin ne ölçtüğü kadar neyi ölçmediği de bilinmelidir."),

  h1("10. Kaynaklar"),
  bullet("Microsoft Learn — What is Foundry Local? (learn.microsoft.com/azure/ai-foundry/foundry-local/)"),
  bullet("Microsoft Learn — Tutorial: Build a RAG application with Foundry Local"),
  bullet("Microsoft Tech Community — Building Your First Local RAG Application with Foundry Local"),
  bullet("Microsoft Learn — Prompt engineering techniques"),
  bullet("SQLite belgeleri — Appropriate Uses For SQLite (sqlite.org)"),
  bullet("Proje tasarım dokümanı: docs/specs/2026-07-03-kisisel-asistan-design.md"),
  bullet("Değerlendirme raporu: docs/eval/degerlendirme-raporu.md"),
];

// ------------------------------------------------------- model tablosu

const MODELS = JSON.parse(fs.readFileSync(path.join(__dirname, "modeller.json"), "utf8"));

const modelTable = table(
  ["Model", "Boyut", "Oto kalite", "Elle kalite", "p50", "Çekimserlik", "Sonuç"],
  MODELS.rows,
  [1740, 900, 1180, 1220, 900, 1200, 2220],
);
const modelNotes = MODELS.notes.map(n => p(n));

const children = [
  ...kapak, ...icindekiler,
  ...govde.flatMap(item => {
    if (item === "__MODEL_TABLE__") return [modelTable];
    if (item === "__MODEL_NOTES__") return modelNotes;
    return [item];
  }),
];

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 }, paragraph: { spacing: { line: 276 } } },
      heading1: { run: { font: "Calibri", size: 32, bold: true, color: "1A1A1A" } },
      heading2: { run: { font: "Calibri", size: 25, bold: true, color: ACCENT } },
    },
  },
  numbering: {
    config: [{
      reference: "madde",
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 460, hanging: 260 } } } },
        { level: 1, format: LevelFormat.BULLET, text: "–", alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 900, hanging: 260 } } } },
      ],
    }],
  },
  features: { updateFields: true },
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: "personas · proje raporu · ", size: 18, color: GRAY }),
                     new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GRAY })],
        })],
      }),
    },
    children,
  }],
});

const out = path.join(__dirname, "personas-proje-raporu.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(out, buf);
  console.log("Yazıldı:", out);
});
