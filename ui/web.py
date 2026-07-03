import os
import sys

# Proje kökünü import yoluna ekle (streamlit run ui/web.py ile çalışsın diye).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st  # noqa: E402

from app import assistant  # noqa: E402

st.set_page_config(page_title="personas", page_icon="🤖")
st.title("🤖 personas — Kişisel Asistan")
st.caption("Offline · Foundry Local · belgelerin + Apple Takvim/Mail")

if "history" not in st.session_state:
    st.session_state.history = []
if "pending" not in st.session_state:
    st.session_state.pending = None

for role, text in st.session_state.history:
    with st.chat_message(role):
        st.write(text)

if st.session_state.pending:
    st.warning("Bu işlemi onaylıyor musun?")
    col1, col2 = st.columns(2)
    if col1.button("✅ Onayla"):
        msg = assistant.confirm(st.session_state.pending)
        st.session_state.history.append(("assistant", msg))
        st.session_state.pending = None
        st.rerun()
    if col2.button("❌ İptal"):
        st.session_state.history.append(("assistant", "İptal edildi."))
        st.session_state.pending = None
        st.rerun()

query = st.chat_input("Bir şey sor...")
if query:
    st.session_state.history.append(("user", query))
    with st.spinner("Düşünüyor..."):
        res = assistant.answer(query)
    text = res["text"]
    if res["sources"]:
        text += f"\n\n_(Kaynak: {', '.join(res['sources'])})_"
    st.session_state.history.append(("assistant", text))
    st.session_state.pending = res["pending_action"]
    st.rerun()
