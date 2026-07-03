"""Orchestrator: route a query, gather context (or build a write draft), answer.

Read queries return {text, sources, pending_action=None}. Write queries return a
draft in `pending_action` and DO NOT execute it — the UI must call confirm().
"""
import re
from datetime import datetime, timedelta

from app import llm, retriever, router
from app.tools import app_launcher, calendar_tool, mail_tool

SYSTEM_PROMPT = (
    "Sen yardımcı bir Türkçe kişisel asistansın. SADECE sana verilen BAĞLAM'ı "
    "kullanarak yanıt ver. Bağlamda cevap yoksa 'Bu konuda bilgim yok.' de. "
    "Mümkünse kaynağı belirt. Kısa, açık ve nazik ol."
)
NO_INFO = "Belgelerimde bu konuda bilgi yok."


def _default_deps():
    return {
        "route": router.route,
        "retrieve": retriever.get_top_chunks,
        "calendar": calendar_tool.get_events,
        "mail": mail_tool.get_recent,
        "chat": llm.chat,
        "create_event": calendar_tool.create_event,
        "send_mail": mail_tool.send_mail,
        "open_app": app_launcher.open_app,
    }


def answer(query, deps=None):
    d = deps or _default_deps()
    decision = d["route"](query)
    tool, action = decision["tool"], decision["action"]

    if tool == "app":
        return _open_app_flow(query, d)

    if action == "write":
        return _draft_write(query, tool, d)

    if tool == "documents":
        chunks = d["retrieve"](query)
        if not chunks:
            return {"text": NO_INFO, "sources": [], "pending_action": None}
        context = "\n\n".join(f"[{s}] {t}" for (s, t, _sc) in chunks)
        text = d["chat"](SYSTEM_PROMPT, f"BAĞLAM:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": [s for (s, _t, _sc) in chunks], "pending_action": None}

    if tool == "calendar":
        events = d["calendar"]()
        context = "\n".join(f"- {e['title']} ({e['start']})" for e in events) or "(etkinlik yok)"
        text = d["chat"](SYSTEM_PROMPT, f"BUGÜNKÜ ETKİNLİKLER:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": ["Apple Takvim"], "pending_action": None}

    if tool == "mail":
        mails = d["mail"]()
        context = "\n".join(f"- {m['subject']} — {m['sender']}" for m in mails) or "(mail yok)"
        text = d["chat"](SYSTEM_PROMPT, f"OKUNMAMIŞ MAİLLER:\n{context}\n\nSORU: {query}")
        return {"text": text, "sources": ["Apple Mail"], "pending_action": None}

    text = d["chat"](SYSTEM_PROMPT, query)
    return {"text": text, "sources": [], "pending_action": None}


def _parse_calendar_draft(query):
    m = re.search(r"(\d{1,2})[:.](\d{2})", query)
    hour, minute = (int(m.group(1)), int(m.group(2))) if m else (9, 0)
    base = datetime.now()
    if "yarın" in query.lower():
        base += timedelta(days=1)
    title = re.sub(r"\d{1,2}[:.]\d{2}", "", query)
    for w in ("yarın", "bugün", "saat", "oluştur", "randevusu", "randevu", "ekle", "kur"):
        title = re.sub(w, "", title, flags=re.IGNORECASE)
    title = title.strip(" ,.-") or "Etkinlik"
    return {
        "type": "calendar", "title": title,
        "year": base.year, "month": base.month, "day": base.day,
        "hour": hour, "minute": minute, "duration_min": 60,
    }


def _draft_mail(query):
    m = re.search(r"[\w.\-]+@[\w.\-]+", query)
    to = m.group(0) if m else None
    subj = re.search(r"'([^']+)'", query) or re.search(r"\"([^\"]+)\"", query)
    subject = subj.group(1) if subj else "(konu yok)"
    body = query.split(":", 1)[1].strip() if ":" in query else "(içerik yok)"
    if not to:
        return {"text": "Kime göndereceğimi anlayamadım. E-posta adresi verir misin?",
                "sources": [], "pending_action": None}
    pa = {"type": "mail", "to": to, "subject": subject, "body": body}
    text = ("Şu e-postayı göndermemi ister misin?\n"
            f"  Kime: {to}\n  Konu: {subject}\n  İçerik: {body}\n(Onaylıyor musun?)")
    return {"text": text, "sources": [], "pending_action": pa}


def _draft_write(query, tool, d):
    if tool == "calendar":
        pa = _parse_calendar_draft(query)
        text = ("Şu etkinliği eklememi ister misin?\n"
                f"  Başlık: {pa['title']}\n"
                f"  Tarih: {pa['day']:02d}.{pa['month']:02d}.{pa['year']} "
                f"{pa['hour']:02d}:{pa['minute']:02d}\n(Onaylıyor musun?)")
        return {"text": text, "sources": [], "pending_action": pa}
    if tool == "mail":
        return _draft_mail(query)
    return {"text": "Bu işlemi yapamıyorum.", "sources": [], "pending_action": None}


def _parse_app_name(query):
    name = re.sub(r"\b(aç|başlat|çalıştır)\b", "", query, flags=re.IGNORECASE)
    name = re.sub(r"'[a-zışçöüğıİ]+", "", name, flags=re.IGNORECASE)  # 'ı 'yi gibi ekleri at
    for w in ("uygulamasını", "uygulamayı", "uygulama", "programını", "lütfen"):
        name = re.sub(w, "", name, flags=re.IGNORECASE)
    return name.strip(" ,.-")


def _open_app_flow(query, d):
    name = _parse_app_name(query)
    opener = d.get("open_app", app_launcher.open_app)
    try:
        opened = opener(name)
        return {"text": f"{opened} uygulamasını açtım. ✓", "sources": [], "pending_action": None}
    except Exception as e:
        return {"text": f"Uygulamayı açamadım: {e}", "sources": [], "pending_action": None}


def confirm(pending_action, deps=None):
    d = deps or _default_deps()
    pa = pending_action
    if pa["type"] == "calendar":
        create = d.get("create_event", calendar_tool.create_event)
        create(pa["title"], pa["year"], pa["month"], pa["day"],
               pa["hour"], pa["minute"], pa["duration_min"])
        return "Etkinlik takvime eklendi. ✓"
    if pa["type"] == "mail":
        send = d.get("send_mail", mail_tool.send_mail)
        send(pa["to"], pa["subject"], pa["body"])
        return "E-posta gönderildi. ✓"
    return "Bilinmeyen işlem."
