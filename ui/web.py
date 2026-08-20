import os
import sys

# Proje kökünü import yoluna ekle (streamlit run ui/web.py ile çalışsın diye).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import html  # noqa: E402

import streamlit as st  # noqa: E402

from app import assistant  # noqa: E402

st.set_page_config(page_title="personas", page_icon="⚡", layout="centered")

CSS = """
<style>
:root { --accent:#F5C518; --accent-dim:#C9A100; --bg:#0E0E0E; --panel:#121212;
        --bot:#1B1B1B; --line:#2a2a2a; --muted:#8A8A8A; }

.stApp { background: var(--bg); }
#MainMenu, footer, header[data-testid="stHeader"] { display:none; }
.block-container { padding-top: 2.0rem; padding-bottom: 6rem; max-width: 820px; }
.ic { width:17px; height:17px; flex:none; }

/* Başlık */
.hdr { text-align:center; margin-bottom:2px; }
.hdr .logo { font-family: ui-monospace, "SF Mono", Menlo, monospace; font-size:2.1rem;
  font-weight:600; color:#fff; }
.hdr .logo .g { color:var(--accent); }
.hdr .sub { color:var(--muted); font-size:0.85rem; margin-top:2px; }
.rule { height:2px; width:60px; margin:14px auto 22px; background:var(--accent); border-radius:2px; }

/* Sohbet */
.chat { display:flex; flex-direction:column; gap:14px; }
.row { display:flex; }
.row.user { justify-content:flex-end; }
.row.bot  { justify-content:flex-start; }
.bubble { max-width:76%; padding:12px 15px; font-size:0.96rem; line-height:1.55; }
.bubble.user { background:var(--accent); color:#141414; border-radius:16px 16px 5px 16px; }
.bubble.bot  { background:var(--bot); color:#EAEAEA; border:1px solid var(--line);
  border-left:3px solid var(--accent); border-radius:5px 16px 16px 5px; }
.bubble.bot code { color:var(--accent); font-size:0.86rem; }
.src-row { margin-top:9px; display:flex; flex-wrap:wrap; gap:6px; }
.pill { font-size:0.7rem; color:var(--accent); border:1px solid var(--accent-dim);
  border-radius:999px; padding:2px 10px; }

/* Onay */
.confirm-note { color:var(--accent); font-weight:500; margin:6px 0 8px 2px; }
div.stButton > button { border-radius:10px; font-weight:500; border:1px solid var(--line);
  background:var(--bot); color:#EAEAEA; }
div.stButton > button:hover { border-color:var(--accent); color:var(--accent); }
div.stButton > button[kind="primary"] { background:var(--accent); color:#141414; border:none; }

/* Giriş kutusu */
[data-testid="stChatInput"] { background:var(--panel); border:1px solid var(--line); border-radius:14px; }
[data-testid="stChatInput"]:focus-within { border-color:var(--accent); }
[data-testid="stChatInput"] textarea { color:#EAEAEA; }

/* Kenar çubuğu */
[data-testid="stSidebar"] { background:var(--panel); border-right:1px solid #222; }
.side-title { color:var(--accent); font-weight:500; letter-spacing:2px; font-size:0.72rem; margin:4px 0 14px 2px; }
.cap { display:flex; gap:11px; align-items:center; padding:9px 0; color:#cfcfcf; font-size:0.86rem; }
.cap .ic { color:var(--accent); }
.side-foot { display:flex; gap:8px; align-items:center; color:#6f6f6f; font-size:0.78rem; margin-top:20px; padding-top:14px; border-top:1px solid #222; }
.side-foot .ic { color:var(--accent); width:15px; height:15px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# İkonlar gömülü SVG: asistan internetsiz çalışmayı vadediyor, arayüzü de öyle
# çalışmalı. İkon fontu daha önce CDN'den geliyordu ve ağ yokken kayboluyordu.
_ICON_BODY = {
    "belge": '<path d="M7 3h6l4 4v14H7z"/><path d="M13 3v4h4"/><path d="M9.5 12h5M9.5 16h5"/>',
    "takvim": '<rect x="4" y="6" width="16" height="14" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "mail": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    "roket": '<path d="M12 3c3 2 5 5.5 5 9l-3 3H10l-3-3c0-3.5 2-7 5-9z"/>'
             '<circle cx="12" cy="10" r="1.6"/><path d="M9 18l-2 3M15 18l2 3"/>',
    "simsek": '<path d="M13 3 6 13h5l-1 8 7-10h-5z"/>',
}


def icon(name, color=None):
    style = f' style="color:{color}"' if color else ""
    return (f'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"{style}>'
            f'{_ICON_BODY[name]}</svg>')



with st.sidebar:
    st.markdown(
        '<div class="side-title">PERSONAS</div>'
        f'<div class="cap">{icon("belge")}<span>Belgelerinden cevap</span></div>'
        f'<div class="cap">{icon("takvim")}<span>Takvim + etkinlik</span></div>'
        f'<div class="cap">{icon("mail")}<span>Mail oku + gönder</span></div>'
        f'<div class="cap">{icon("roket")}<span>Uygulama açar</span></div>'
        f'<div class="side-foot">{icon("simsek")}<span>Offline · Foundry Local</span></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="hdr">'
    f'<div class="logo">{icon("simsek", "#F5C518")} <span class="g">person</span>as</div>'
    '<div class="sub">offline kişisel asistanın — belgelerin, takvimin, mailin</div>'
    '</div><div class="rule"></div>',
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

if not st.session_state.history:
    st.session_state.history.append(
        ("assistant", "Merhaba! Belgelerin, takvimin ve mailin hakkında soru sorabilir; "
                      "\"yarın 15:00 toplantı ekle\" ya da \"Spotify aç\" gibi işlemler isteyebilirsin.", None)
    )


def bubble_html(role, text, sources):
    cls = "user" if role == "user" else "bot"
    safe = html.escape(text).replace("\n", "<br>")
    src = ""
    if sources:
        chips = "".join(f'<span class="pill">{html.escape(s)}</span>' for s in sources)
        src = f'<div class="src-row">{chips}</div>'
    return f'<div class="row {cls}"><div class="bubble {cls}">{safe}{src}</div></div>'


chat_html = "".join(bubble_html(r, t, s) for (r, t, s) in st.session_state.history)
st.markdown(f'<div class="chat">{chat_html}</div>', unsafe_allow_html=True)

if st.session_state.pending:
    st.markdown('<div class="confirm-note">⚠️ Bu işlemi onaylıyor musun?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Onayla", type="primary", use_container_width=True):
        msg = assistant.confirm(st.session_state.pending)
        st.session_state.history.append(("assistant", msg, None))
        st.session_state.pending = None
        st.rerun()
    if c2.button("İptal", use_container_width=True):
        st.session_state.history.append(("assistant", "İptal edildi.", None))
        st.session_state.pending = None
        st.rerun()

query = st.chat_input("Bir şey sor ya da bir işlem iste...")
if query:
    # Kullanıcı balonu hemen görünsün, cevap ise geldikçe yazılsın.
    st.markdown(f'<div class="chat">{bubble_html("user", query, None)}</div>',
                unsafe_allow_html=True)
    yer = st.empty()
    gecmis = [(rol, metin) for (rol, metin, _kaynak) in st.session_state.history]
    st.session_state.history.append(("user", query, None))

    parcalar, res = [], None
    for olay in assistant.answer_stream(query, history=gecmis):
        if olay["type"] == "token":
            parcalar.append(olay["text"])
            yer.markdown(
                f'<div class="chat">{bubble_html("assistant", "".join(parcalar), None)}</div>',
                unsafe_allow_html=True)
        else:
            res = olay["result"]

    st.session_state.history.append(("assistant", res["text"], res["sources"] or None))
    st.session_state.pending = res["pending_action"]
    st.rerun()
