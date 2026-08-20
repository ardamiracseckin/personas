/* personas arayüzü — bağımlılık yok, derleme yok, ağ çağrısı yok. */

const state = {
  conversationId: null,
  conversations: [],
  documents: [],
  streaming: false,
  abort: null,
};

const $ = (sel) => document.querySelector(sel);
const messagesEl = $("#messages");
const inputEl = $("#input");

const ICON = {
  bolt: '<path d="M13 3 6 13h5l-1 8 7-10h-5z"/>',
  trash: '<path d="M5 7h14M10 7V5h4v2M7 7l1 12h8l1-12"/>',
  pen: '<path d="M4 20h4L19 9a2 2 0 0 0-3-3L5 17z"/>',
};
const icon = (name) =>
  `<svg class="ic" viewBox="0 0 24 24">${ICON[name]}</svg>`;

const SUGGESTIONS = [
  ["Ekran görüntüsünü belirli bir bölgeden nasıl alırım?", "belgelerinden cevap"],
  ["Git'te son commit'i geri alıp değişiklikleri nasıl korurum?", "kaynak göstererek"],
  ["Yarın 15:00 dişçi randevusu ekle", "onayınla takvime yazar"],
  ["Bugün takvimimde ne var?", "Apple Takvim'i okur"],
];

/* ------------------------------------------------------------------ istekler */

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: options.body instanceof FormData ? {} : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

function toast(message) {
  const el = $("#toast");
  el.textContent = message;
  el.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { el.hidden = true; }, 5000);
}

/* --------------------------------------------------------------- markdown */

function escapeHtml(text) {
  return text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}

const KEYWORDS = {
  bash: ["cd", "ls", "git", "python3", "python", "pip", "source", "brew", "foundry",
         "sudo", "echo", "grep", "mkdir", "rm", "cp", "mv", "curl", "uvicorn", "pytest", "open"],
  python: ["def", "return", "import", "from", "class", "if", "else", "elif", "for", "while",
           "try", "except", "with", "as", "None", "True", "False", "lambda", "yield", "in", "not"],
  sql: ["select", "from", "where", "insert", "into", "values", "create", "table", "not",
        "exists", "delete", "update", "set", "order", "by", "group", "count", "primary", "key"],
};

/* Sıra önemli: önce anahtar kelimeler, sonra dizgeler, sonra yorumlar.
   Üretilen etiketlerde tırnak kullanılmıyor (class=k) ki dizge deseni onlara takılmasın. */
function highlight(code, lang) {
  let out = code;
  const words = KEYWORDS[lang];
  if (words) {
    out = out.replace(new RegExp(`\\b(${words.join("|")})\\b`, "g"), "<span class=k>$1</span>");
  }
  out = out.replace(/('[^'\n]*'|"[^"\n]*")/g, "<span class=s>$1</span>");
  out = out.replace(/(^|\n)(\s*(?:#|--)[^\n]*)/g, "$1<span class=c>$2</span>");
  return out;
}

function inlineMarkdown(text) {
  return text
    .replace(/`([^`]+)`/g, (_, c) => `<code>${c}</code>`)
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>");
}

function renderMarkdown(source) {
  const blocks = [];
  let text = source.replace(/```([\w+-]*)\n?([\s\S]*?)```/g, (_, lang, code) => {
    blocks.push({ lang: (lang || "").toLowerCase(), code: code.replace(/\n$/, "") });
    return `\u241E${blocks.length - 1}\u241E`;
  });
  text = escapeHtml(text);

  const out = [];
  let list = null;
  const closeList = () => { if (list) { out.push(`</${list}>`); list = null; } };
  const openList = (tag) => { if (list !== tag) { closeList(); out.push(`<${tag}>`); list = tag; } };

  for (const line of text.split("\n")) {
    const placeholder = line.trim().match(/^\u241E(\d+)\u241E$/);
    if (placeholder) { closeList(); out.push(codeBlockHtml(blocks[+placeholder[1]])); continue; }

    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) { closeList(); out.push(`<h4>${inlineMarkdown(heading[2])}</h4>`); continue; }

    const bullet = line.match(/^\s*[-*+]\s+(.*)$/);
    if (bullet) { openList("ul"); out.push(`<li>${inlineMarkdown(bullet[1])}</li>`); continue; }

    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (numbered) { openList("ol"); out.push(`<li>${inlineMarkdown(numbered[1])}</li>`); continue; }

    const quote = line.match(/^&gt;\s?(.*)$/);
    if (quote) { closeList(); out.push(`<blockquote>${inlineMarkdown(quote[1])}</blockquote>`); continue; }

    if (!line.trim()) { closeList(); continue; }
    closeList();
    out.push(`<p>${inlineMarkdown(line)}</p>`);
  }
  closeList();
  return out.join("");
}

function codeBlockHtml({ lang, code }) {
  const etiket = lang || "kod";
  return `<pre class="code"><div class="code-head"><span>${etiket}</span>` +
    `<button class="copy" data-code="${encodeURIComponent(code)}">kopyala</button></div>` +
    `<code>${highlight(escapeHtml(code), lang)}</code></pre>`;
}

/* --------------------------------------------------------------- mesajlar */

function messageEl(role) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${role}`;
  if (role === "assistant") {
    wrap.innerHTML = `<div class="avatar">${icon("bolt")}</div><div class="body"></div>`;
  } else {
    wrap.innerHTML = `<div class="body"></div>`;
  }
  return wrap;
}

function thread() {
  let el = messagesEl.querySelector(".thread");
  if (!el) {
    messagesEl.innerHTML = '<div class="thread"></div>';
    el = messagesEl.querySelector(".thread");
  }
  return el;
}

function appendMessage(role, text, sources, chunks, pending) {
  const el = messageEl(role);
  const body = el.querySelector(".body");
  body.innerHTML = role === "assistant" ? renderMarkdown(text) : escapeHtml(text);
  if (role === "assistant") decorateAssistant(body, { text, sources, chunks, pending });
  thread().appendChild(el);
  scrollToBottom();
  return el;
}

function decorateAssistant(body, { text, sources = [], chunks = [], pending }) {
  const benzersiz = [...new Set(sources)];
  if (benzersiz.length) {
    const row = document.createElement("div");
    row.className = "sources";
    for (const kaynak of benzersiz) {
      const b = document.createElement("button");
      b.className = "pill";
      b.textContent = kaynak;
      b.onclick = () => toggleChunks(body, kaynak, chunks);
      row.appendChild(b);
    }
    body.appendChild(row);
  }

  if (pending) body.appendChild(confirmCard(pending));

  const actions = document.createElement("div");
  actions.className = "msg-actions";
  actions.innerHTML =
    '<button class="act" data-act="copy">kopyala</button>' +
    '<button class="act" data-act="regen">yeniden üret</button>';
  actions.querySelector('[data-act="copy"]').onclick = (e) => {
    navigator.clipboard.writeText(text);
    e.target.textContent = "kopyalandı";
    setTimeout(() => { e.target.textContent = "kopyala"; }, 1500);
  };
  actions.querySelector('[data-act="regen"]').onclick = () => regenerate();
  body.appendChild(actions);
}

function toggleChunks(body, kaynak, chunks) {
  const varolan = body.querySelector(`.chunk-panel[data-source="${CSS.escape(kaynak)}"]`);
  if (varolan) { varolan.remove(); return; }
  const ilgili = (chunks || []).filter((c) => c.source === kaynak);
  const panel = document.createElement("div");
  panel.className = "chunk-panel";
  panel.dataset.source = kaynak;
  panel.innerHTML = ilgili.length
    ? ilgili.map((c) =>
        `<div class="chunk-head"><span>${escapeHtml(c.source)}</span>` +
        `<span>benzerlik ${c.score}</span></div>${escapeHtml(c.text)}`).join("<hr>")
    : "Bu cevapta gösterilecek parça metni yok.";
  body.appendChild(panel);
}

function confirmCard(pending) {
  const kart = document.createElement("div");
  kart.className = "confirm-card";
  const satirlar = pending.type === "calendar"
    ? [["Başlık", pending.title],
       ["Tarih", `${String(pending.day).padStart(2, "0")}.${String(pending.month).padStart(2, "0")}.${pending.year}`],
       ["Saat", `${String(pending.hour).padStart(2, "0")}:${String(pending.minute).padStart(2, "0")}`],
       ["Süre", `${pending.duration_min} dk`]]
    : [["Kime", pending.to], ["Konu", pending.subject], ["İçerik", pending.body]];

  kart.innerHTML =
    `<strong>${pending.type === "calendar" ? "Takvime eklenecek" : "Gönderilecek e-posta"}</strong>` +
    `<div class="rows">${satirlar.map(([k, v]) => `${k}: ${escapeHtml(String(v ?? ""))}`).join("<br>")}</div>` +
    '<div class="buttons"><button class="btn primary">Onayla</button><button class="btn">İptal</button></div>';

  const [onayla, iptal] = kart.querySelectorAll("button");
  onayla.onclick = async () => {
    onayla.disabled = true;
    try {
      const sonuc = await api("/api/confirm", {
        method: "POST",
        body: JSON.stringify({ conversation_id: state.conversationId, pending_action: pending }),
      });
      kart.replaceWith(Object.assign(document.createElement("p"), { textContent: sonuc.message }));
    } catch (e) {
      toast(e.message);
      onayla.disabled = false;
    }
  };
  iptal.onclick = () => {
    kart.replaceWith(Object.assign(document.createElement("p"), { textContent: "İptal edildi." }));
  };
  return kart;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

/* ------------------------------------------------------------------ sohbet */

async function send(text, { regenerate = false } = {}) {
  if (state.streaming) return;
  if (!state.conversationId) await newConversation({ silent: true });

  if (!regenerate) appendMessage("user", text);
  const el = appendMessage("assistant", "");
  const body = el.querySelector(".body");
  body.innerHTML = '<span class="typing"><i></i><i></i><i></i></span>';

  state.streaming = true;
  state.abort = new AbortController();
  $("#send").hidden = true;
  $("#stop").hidden = false;

  let biriken = "";
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        conversation_id: state.conversationId,
        message: regenerate ? null : text,
        regenerate,
      }),
      signal: state.abort.signal,
    });
    if (!res.ok) throw new Error((await res.json()).detail || "İstek başarısız");

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let tampon = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      tampon += decoder.decode(value, { stream: true });
      const parcalar = tampon.split("\n\n");
      tampon = parcalar.pop();
      for (const parca of parcalar) {
        if (!parca.startsWith("data: ")) continue;
        const olay = JSON.parse(parca.slice(6));
        if (olay.type === "token") {
          biriken += olay.text;
          body.textContent = biriken;      // akış sırasında düz metin
          scrollToBottom();
        } else if (olay.type === "final") {
          const r = olay.result;
          body.innerHTML = renderMarkdown(r.text);
          decorateAssistant(body, {
            text: r.text, sources: r.sources, chunks: r.chunks, pending: r.pending_action,
          });
          scrollToBottom();
        } else if (olay.type === "title") {
          $("#chat-title").textContent = olay.title;
          await loadConversations();
        } else if (olay.type === "error") {
          body.innerHTML = `<p>${escapeHtml(olay.message)}</p>`;
          toast(olay.message);
        }
      }
    }
  } catch (e) {
    if (e.name === "AbortError") {
      body.innerHTML = renderMarkdown(biriken || "_(durduruldu)_");
    } else {
      body.innerHTML = `<p>${escapeHtml(e.message)}</p>`;
      toast(e.message);
    }
  } finally {
    state.streaming = false;
    state.abort = null;
    $("#send").hidden = false;
    $("#stop").hidden = true;
    inputEl.focus();
  }
}

function regenerate() {
  if (state.streaming) return;
  const sonAsistan = [...thread().querySelectorAll(".msg.assistant")].pop();
  if (sonAsistan) sonAsistan.remove();
  send(null, { regenerate: true });
}

/* ------------------------------------------------------------- konuşmalar */

async function loadConversations() {
  state.conversations = await api("/api/conversations");
  const liste = $("#conversations");
  liste.innerHTML = "";
  for (const konusma of state.conversations) {
    const el = document.createElement("div");
    el.className = "conv" + (konusma.id === state.conversationId ? " active" : "");
    el.innerHTML =
      `<span class="conv-title">${escapeHtml(konusma.title)}</span>` +
      `<span class="conv-actions">` +
      `<button class="mini" data-act="rename" title="Yeniden adlandır">${icon("pen")}</button>` +
      `<button class="mini" data-act="delete" title="Sil">${icon("trash")}</button></span>`;
    el.onclick = (e) => {
      const act = e.target.closest("[data-act]")?.dataset.act;
      if (act === "rename") return renameConversation(konusma);
      if (act === "delete") return deleteConversation(konusma);
      openConversation(konusma.id);
    };
    liste.appendChild(el);
  }
}

async function newConversation({ silent = false } = {}) {
  const yeni = await api("/api/conversations", { method: "POST", body: JSON.stringify({}) });
  state.conversationId = yeni.id;
  $("#chat-title").textContent = yeni.title;
  if (!silent) renderWelcome();
  await loadConversations();
  inputEl.focus();
}

async function openConversation(id) {
  state.conversationId = id;
  const konusma = state.conversations.find((c) => c.id === id);
  $("#chat-title").textContent = konusma ? konusma.title : "Sohbet";
  const mesajlar = await api(`/api/conversations/${id}/messages`);
  messagesEl.innerHTML = '<div class="thread"></div>';
  if (!mesajlar.length) renderWelcome();
  for (const m of mesajlar) appendMessage(m.role, m.text, m.sources, [], null);
  await loadConversations();
}

async function renameConversation(konusma) {
  const yeni = prompt("Yeni ad:", konusma.title);
  if (!yeni) return;
  await api(`/api/conversations/${konusma.id}`, {
    method: "PATCH", body: JSON.stringify({ title: yeni }),
  });
  if (konusma.id === state.conversationId) $("#chat-title").textContent = yeni;
  await loadConversations();
}

async function deleteConversation(konusma) {
  await api(`/api/conversations/${konusma.id}`, { method: "DELETE" });
  if (konusma.id === state.conversationId) {
    state.conversationId = null;
    renderWelcome();
    $("#chat-title").textContent = "Yeni sohbet";
  }
  await loadConversations();
}

function renderWelcome() {
  messagesEl.innerHTML =
    '<div class="welcome"><h2>Merhaba, ben <span>personas</span></h2>' +
    "<p>Belgelerin, takvimin ve mailin hakkında sorabilirsin. Her şey bu bilgisayarda çalışır.</p>" +
    '<div class="suggestions"></div></div>';
  const kutu = messagesEl.querySelector(".suggestions");
  for (const [soru, aciklama] of SUGGESTIONS) {
    const b = document.createElement("button");
    b.className = "suggestion";
    b.innerHTML = `${escapeHtml(soru)}<small>${aciklama}</small>`;
    b.onclick = () => { inputEl.value = soru; submit(); };
    kutu.appendChild(b);
  }
}

/* --------------------------------------------------------------- belgeler */

async function loadDocuments() {
  state.documents = await api("/api/documents");
  const liste = $("#documents");
  liste.innerHTML = "";
  if (!state.documents.length) {
    liste.innerHTML = '<div class="hint">Henüz belge yok. Sürükleyip bırakabilirsin.</div>';
    return;
  }
  for (const belge of state.documents) {
    const el = document.createElement("div");
    el.className = "doc";
    el.innerHTML =
      `<span class="doc-name" title="${escapeHtml(belge.name)}">${escapeHtml(belge.name)}</span>` +
      `<span class="doc-count">${belge.chunks}</span>` +
      `<button class="doc-x" title="Kaldır">${icon("trash")}</button>`;
    el.querySelector(".doc-x").onclick = async () => {
      await api(`/api/documents/${encodeURIComponent(belge.name)}`, { method: "DELETE" });
      loadDocuments();
    };
    liste.appendChild(el);
  }
}

async function uploadFiles(files) {
  for (const dosya of files) {
    const form = new FormData();
    form.append("file", dosya);
    try {
      const sonuc = await api("/api/documents", { method: "POST", body: form });
      toast(`${sonuc.name}: ${sonuc.chunks} parça eklendi`);
    } catch (e) {
      toast(`${dosya.name}: ${e.message}`);
    }
  }
  loadDocuments();
}

/* ---------------------------------------------------------------- modeller */

async function loadModels() {
  const katalog = await api("/api/models");
  const secim = $("#model-select");
  secim.innerHTML = "";
  for (const model of katalog) {
    const o = document.createElement("option");
    o.value = model.alias;
    o.textContent = `${model.alias} · ${model.boyut}${model.indirildi ? "" : " (indirilmemiş)"}`;
    o.selected = model.aktif;
    secim.appendChild(o);
  }
  const aktif = katalog.find((m) => m.aktif);
  $("#model-note").textContent = aktif ? aktif.not : "";
}

async function switchModel(alias) {
  const not = $("#model-note");
  not.textContent = "Model değiştiriliyor, bu 20-30 saniye sürebilir…";
  try {
    await api("/api/models", { method: "POST", body: JSON.stringify({ alias }) });
    toast(`${alias} yüklendi`);
  } catch (e) {
    toast(e.message);
  }
  loadModels();
}

/* -------------------------------------------------------------- olay bağları */

function submit() {
  const metin = inputEl.value.trim();
  if (!metin || state.streaming) return;
  inputEl.value = "";
  inputEl.style.height = "auto";
  if (messagesEl.querySelector(".welcome")) messagesEl.innerHTML = '<div class="thread"></div>';
  send(metin);
}

$("#composer").addEventListener("submit", (e) => { e.preventDefault(); submit(); });
$("#new-chat").onclick = () => newConversation();
$("#stop").onclick = () => state.abort?.abort();
$("#attach").onclick = () => $("#doc-input").click();
$("#add-doc").onclick = () => $("#doc-input").click();
$("#doc-input").onchange = (e) => uploadFiles(e.target.files);
$("#model-select").onchange = (e) => switchModel(e.target.value);

inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); }
});
inputEl.addEventListener("input", () => {
  inputEl.style.height = "auto";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 180) + "px";
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape" && state.streaming) state.abort?.abort();
  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); newConversation(); }
});

document.addEventListener("click", (e) => {
  const kopyala = e.target.closest(".copy");
  if (!kopyala) return;
  navigator.clipboard.writeText(decodeURIComponent(kopyala.dataset.code));
  kopyala.textContent = "kopyalandı";
  kopyala.classList.add("done");
  setTimeout(() => { kopyala.textContent = "kopyala"; kopyala.classList.remove("done"); }, 1500);
});

["dragenter", "dragover"].forEach((tip) =>
  document.addEventListener(tip, (e) => { e.preventDefault(); document.body.classList.add("dragging"); }));
["dragleave", "drop"].forEach((tip) =>
  document.addEventListener(tip, (e) => {
    e.preventDefault();
    if (tip === "drop" || e.relatedTarget === null) document.body.classList.remove("dragging");
  }));
document.addEventListener("drop", (e) => {
  if (e.dataTransfer?.files?.length) uploadFiles(e.dataTransfer.files);
});

/* ------------------------------------------------------------------ açılış */

(async function init() {
  await loadModels();
  await loadDocuments();
  await loadConversations();
  if (state.conversations.length) {
    await openConversation(state.conversations[0].id);
  } else {
    renderWelcome();
  }
  inputEl.focus();
})();
