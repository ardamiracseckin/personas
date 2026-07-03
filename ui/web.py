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
:root { --accent:#F5C518; --accent-dim:#C9A100; --bg:#0E0E0E; --panel:#161616; --muted:#9A9A9A; }

/* Genel arka plan */
.stApp { background: radial-gradient(1200px 600px at 50% -10%, #1a1a1a 0%, var(--bg) 55%); }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }
.block-container { padding-top: 2.2rem; max-width: 820px; }

/* Başlık */
.app-header { text-align:center; margin-bottom: 0.4rem; }
.app-header .logo {
  font-size: 2.6rem; font-weight: 800; letter-spacing: -1px;
  color: #fff;
}
.app-header .logo .p { color: var(--accent); }
.app-header .bolt { color: var(--accent); }
.app-header .sub { color: var(--muted); font-size: 0.92rem; margin-top: 2px; }
.divider { height:3px; width:70px; margin:14px auto 24px auto;
  background: linear-gradient(90deg, transparent, var(--accent), transparent); border-radius:3px; }

/* Sohbet balonları */
.chat { display:flex; flex-direction:column; gap:14px; margin-bottom: 90px; }
.row { display:flex; }
.row.user { justify-content:flex-end; }
.row.bot  { justify-content:flex-start; }

.bubble { max-width: 78%; padding: 12px 16px; border-radius: 16px; line-height:1.5;
  font-size: 0.98rem; box-shadow: 0 2px 10px rgba(0,0,0,0.35); animation: pop .18s ease-out; }
@keyframes pop { from { transform: translateY(6px); opacity:0 } to { transform:none; opacity:1 } }

.bubble.user { background: var(--accent); color:#141414; border-bottom-right-radius:5px; font-weight:500; }
.bubble.bot  { background:#1B1B1B; color:#EAEAEA; border:1px solid #2a2a2a;
  border-left:3px solid var(--accent); border-bottom-left-radius:5px; }

.src-row { margin-top:10px; display:flex; flex-wrap:wrap; gap:6px; }
.source-badge { font-size:0.72rem; color:var(--accent); border:1px solid var(--accent-dim);
  border-radius:999px; padding:2px 10px; background:rgba(245,197,24,0.08); }

/* Onay kutusu */
.confirm-note { color:var(--accent); font-weight:600; margin: 4px 0 8px 2px; }

/* Butonlar */
div.stButton > button { border-radius:10px; font-weight:700; border:1px solid #2a2a2a;
  background:#1B1B1B; color:#EAEAEA; }
div.stButton > button:hover { border-color:var(--accent); color:var(--accent); }
div.stButton > button[kind="primary"] { background:var(--accent); color:#141414; border:none; }

/* Sohbet girişi */
[data-testid="stChatInput"] { border:1px solid #2a2a2a; border-radius:14px; background:var(--panel); }
[data-testid="stChatInput"]:focus-within { border-color:var(--accent); }

/* Kenar çubuğu */
[data-testid="stSidebar"] { background:#121212; border-right:1px solid #222; }
.cap { display:flex; gap:10px; align-items:flex-start; padding:9px 0; color:#cfcfcf; font-size:0.9rem; }
.cap .ic { color:var(--accent); font-size:1.05rem; width:20px; }
.side-title { color:var(--accent); font-weight:800; letter-spacing:.5px; font-size:0.8rem;
  text-transform:uppercase; margin: 6px 0 4px 2px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# Kenar çubuğu — yetenekler
with st.sidebar:
    st.markdown('<div class="side-title">personas</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="cap"><span class="ic">📄</span><span>Belgelerinden kaynak göstererek cevap</span></div>'
        '<div class="cap"><span class="ic">📅</span><span>Takvimini okur, onayınla etkinlik ekler</span></div>'
        '<div class="cap"><span class="ic">✉️</span><span>Mailini okur, onayınla e-posta gönderir</span></div>'
        '<div class="cap"><span class="ic">🚀</span><span>Uygulama açar ("Spotify aç")</span></div>'
        '<div class="cap"><span class="ic">⚡</span><span>Tamamen offline · Foundry Local</span></div>',
        unsafe_allow_html=True,
    )

# Başlık
st.markdown(
    '<div class="app-header">'
    '<div class="logo"><span class="bolt">⚡</span> <span class="p">person</span>as</div>'
    '<div class="sub">Offline kişisel asistanın — belgelerin, takvimin ve mailin tek yerde</div>'
    '</div><div class="divider"></div>',
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []  # list of (role, text, sources)
if "pending" not in st.session_state:
    st.session_state.pending = None


def bubble_html(role, text, sources):
    cls = "user" if role == "user" else "bot"
    safe = html.escape(text).replace("\n", "<br>")
    src = ""
    if sources:
        chips = "".join(f'<span class="source-badge">{html.escape(s)}</span>' for s in sources)
        src = f'<div class="src-row">{chips}</div>'
    return f'<div class="row {cls}"><div class="bubble {cls}">{safe}{src}</div></div>'


if not st.session_state.history:
    st.session_state.history.append(
        ("assistant", "Merhaba! Ben personas. Belgelerin, takvimin ve mailin hakkında "
                      "soru sorabilir; \"yarın 15:00 toplantı ekle\" gibi işlemler isteyebilirsin.", None)
    )

chat_html = "".join(bubble_html(r, t, s) for (r, t, s) in st.session_state.history)
st.markdown(f'<div class="chat">{chat_html}</div>', unsafe_allow_html=True)

# Bekleyen onay
if st.session_state.pending:
    st.markdown('<div class="confirm-note">⚠️ Bu işlemi onaylıyor musun?</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("✅ Onayla", type="primary", use_container_width=True):
        msg = assistant.confirm(st.session_state.pending)
        st.session_state.history.append(("assistant", msg, None))
        st.session_state.pending = None
        st.rerun()
    if c2.button("❌ İptal", use_container_width=True):
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
