/* Mevzuat asistanı arayüzü — bağımlılıksız.
   Asistan cevap üretmediği için burada da tek kelime üretilmez: ekrana yazılan
   her şey sunucudan gelen kanun metnidir. */

const $ = (s) => document.querySelector(s);
const akis = $("#akis");
const acilis = $("#acilis");
const form = $("#form");
const giris = $("#giris");
const gonder = $("#gonder");

let mesgul = false;

function kacir(metin) {
  const d = document.createElement("div");
  d.textContent = metin ?? "";
  return d.innerHTML;
}

/* ---------------------------------------------------------------- çizimler */

function turEkle(soru) {
  acilis.hidden = true;
  akis.hidden = false;
  const tur = document.createElement("article");
  tur.className = "tur";
  tur.innerHTML = `<div class="soru">${kacir(soru)}</div>
                   <div class="govde"><p class="bekliyor">kanun metinlerinde arıyorum…</p></div>`;
  akis.appendChild(tur);
  tur.scrollIntoView({ behavior: "smooth", block: "start" });
  return tur.querySelector(".govde");
}

/* Maddenin tam metni gösterilir, soruyla en çok örtüşen cümle içinde işaretlenir.
   Yalnızca cümleyi göstermek yanıltıcı olurdu: hukukta bir fıkra, komşusu
   okunmadan anlaşılmaz. Metin kısaltılmaz; işaretlenen kısım da metnin kendisidir. */
function metniIsaretle(metin, cumle) {
  const tam = kacir(metin);
  const hedef = kacir((cumle || "").trim());
  if (!hedef || hedef.length < 12) return tam;
  const yer = tam.indexOf(hedef);
  if (yer < 0) return tam;
  // Vurgu metnin neredeyse tamamını kaplıyorsa hiçbir şey söylemiyor demektir:
  // tek cümlelik maddelerde işaretleme bırakılır.
  if (hedef.length > tam.length * 0.8) return tam;
  return tam.slice(0, yer) + `<mark>${hedef}</mark>` + tam.slice(yer + hedef.length);
}

function birincilKart(a) {
  const kart = document.createElement("div");
  kart.className = "birincil";
  kart.innerHTML =
    `<div class="olcu">benzerlik ${a.puan.toFixed(2)}</div>
     <div class="atif">${kacir(a.atif)}</div>
     <div class="baslik">${kacir(a.baslik) || "&nbsp;"}</div>
     <div class="madde-metni">${metniIsaretle(a.metin, a.one_cikan)}</div>`;
  return kart;
}

function digerleriListesi(adaylar) {
  const sarmal = document.createElement("div");
  sarmal.className = "digerleri";
  sarmal.innerHTML = `<div class="etiket">diğer adaylar · alaka sırasıyla</div>`;
  adaylar.forEach((a, i) => {
    const satir = document.createElement("div");
    satir.className = "aday";
    satir.innerHTML =
      `<button class="aday-bas" type="button">
         <span class="sira">${i + 2}.</span>
         <span class="ad">${kacir(a.atif)}</span>
         <span class="bas">${kacir(a.baslik)}</span>
         <span class="puan">${a.puan.toFixed(2)}</span>
       </button>
       <div class="govde">${kacir(a.metin)}</div>`;
    satir.querySelector(".aday-bas").onclick = () => satir.classList.toggle("acik");
    sarmal.appendChild(satir);
  });
  return sarmal;
}

function durumKutusu(metin, uyari) {
  const d = document.createElement("div");
  d.className = "durum-kutu" + (uyari ? " uyari" : "");
  d.innerHTML = metin;
  return d;
}

function ciz(govde, veri) {
  govde.innerHTML = "";
  if (veri.durum === "kapsam_disi") {
    govde.appendChild(durumKutusu(
      `<strong>Bu soruya madde göstermiyorum.</strong><br>${kacir(veri.mesaj)}`, true));
    return;
  }
  if (veri.durum === "bulunamadi") {
    govde.appendChild(durumKutusu(
      "<strong>Yüklü kanunlarda bu konuyla ilgili bir madde bulamadım.</strong><br>" +
      "Sorunu farklı kelimelerle deneyebilirsin; konu yüklü kanunların dışındaysa " +
      "bu asistan yardımcı olamaz."));
    return;
  }
  govde.appendChild(durumKutusu(
    "<strong>En yakın madde bu.</strong> Aşağıdaki cümle, sorunla en çok örtüşen " +
    "kısım — ama karar senin: maddenin tamamını okumadan sonuç çıkarma.", true));
  const etiket = document.createElement("div");
  etiket.className = "etiket";
  etiket.style.marginTop = "20px";
  etiket.textContent = "en yakın madde";
  govde.appendChild(etiket);
  govde.appendChild(birincilKart(veri.birincil));
  if (veri.digerleri.length) govde.appendChild(digerleriListesi(veri.digerleri));
}

/* ------------------------------------------------------------------- akış */

async function sor(soru) {
  if (mesgul || !soru.trim()) return;
  mesgul = true;
  gonder.disabled = true;
  giris.value = "";
  const govde = turEkle(soru);
  try {
    const cevap = await fetch("/api/mevzuat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: soru }),
    });
    const veri = await cevap.json();
    if (!cevap.ok) throw new Error(veri.detail || "İstek başarısız oldu.");
    ciz(govde, veri);
  } catch (e) {
    govde.innerHTML = `<p class="hata">${kacir(e.message)}</p>`;
  } finally {
    mesgul = false;
    gonder.disabled = false;
    giris.focus();
  }
}

form.onsubmit = (e) => { e.preventDefault(); sor(giris.value); };
document.querySelectorAll("#ornekler button").forEach((b) => {
  b.onclick = () => sor(b.textContent.trim());
});

/* ---------------------------------------------------------------- açılışta */

(async function kunyeyiOku() {
  try {
    const d = await (await fetch("/api/mevzuat/kanunlar")).json();
    $("#kunye").textContent = `${d.parca} madde parçası · ${d.kanunlar.length} kanun`;
    $("#kanunlar").innerHTML = d.kanunlar
      .map((k) => `<span>${kacir(k.ad)}</span>`).join("");
  } catch {
    $("#kunye").textContent = "bilgi tabanına ulaşılamadı";
  }
  const bagdaki = new URLSearchParams(location.search).get("soru");
  if (bagdaki) { sor(bagdaki); return; }
  giris.focus();
})();
