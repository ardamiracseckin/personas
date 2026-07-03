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
@import url('https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@3/dist/tabler-icons.min.css');
:root { --accent:#F5C518; --accent-dim:#C9A100; --bg:#0E0E0E; --panel:#121212;
        --bot:#1B1B1B; --line:#2a2a2a; --muted:#8A8A8A; }

.stApp { background: var(--bg); }
#MainMenu, footer, header[data-testid="stHeader"] { display:none; }
.block-container { padding-top: 2.0rem; padding-bottom: 6rem; max-width: 820px; }
.ti { font-size: 17px; line-height: 1; }

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
.cap .ti { color:var(--accent); }
.side-foot { display:flex; gap:8px; align-items:center; color:#6f6f6f; font-size:0.78rem; margin-top:20px; padding-top:14px; border-top:1px solid #222; }
.side-foot .ti { color:var(--accent); font-size:15px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown(
        '<div class="side-title">PERSONAS</div>'
        '<div class="cap"><i class="ti ti-file-text"></i><span>Belgelerinden cevap</span></div>'
        '<div class="cap"><i class="ti ti-calendar"></i><span>Takvim + etkinlik</span></div>'
        '<div class="cap"><i class="ti ti-mail"></i><span>Mail oku + gönder</span></div>'
        '<div class="cap"><i class="ti ti-rocket"></i><span>Uygulama açar</span></div>'
        '<div class="side-foot"><i class="ti ti-bolt"></i><span>Offline · Foundry Local</span></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    '<div class="hdr">'
    '<div class="logo"><i class="ti ti-bolt" style="color:#F5C518"></i> <span class="g">person</span>as</div>'
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
    st.session_state.history.append(("user", query, None))
    with st.spinner("Düşünüyor..."):
        res = assistant.answer(query)
    st.session_state.history.append(("assistant", res["text"], res["sources"] or None))
    st.session_state.pending = res["pending_action"]
    st.rerun()
