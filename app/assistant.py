"""Orchestrator: route a query, gather context (or build a write draft), answer.

Read queries return {text, sources, pending_action=None}. Write queries return a
draft in `pending_action` and DO NOT execute it — the UI must call confirm().
"""
import re
from datetime import datetime, timedelta

from app import llm, retriever, router
from app.tools import app_launcher, calendar_tool, mail_tool

SYSTEM_PROMPT = (
    "Sen 'personas' adlı yardımcı bir kişisel asistansın. HER ZAMAN akıcı ve "
    "dilbilgisi açısından doğru TÜRKÇE yazarsın. Kurallar:\n"
    "- Yalnızca sana verilen BAĞLAM'daki bilgiyi kullan; bağlamda yoksa "
    "'Bu konuda bilgim yok.' de ve asla uydurma.\n"
    "- Kısa, net ve doğrudan ol; soruyu tekrarlama, gereksiz cümle kurma.\n"
    "- Komut veya kod verirken bozmadan, doğru biçimde yaz."
)
NO_INFO = "Belgelerimde bu konuda bilgi yok."


MAX_HISTORY_TURNS = 4  # son iki soru-cevap; küçük modelde daha fazlası dikkati dağıtıyor

# Takip soruları kendi başına anlamsızdır ("peki bunu nasıl geri alırım?");
# erişim için önceki soruyla birleştirilirler. Uzunluğa değil, işaret zamirine
# bakılır: kısa ama kendi başına anlamlı sorular ("RAG nedir?") bozulmasın.
_FOLLOW_UP_RE = re.compile(
    r"\b(bunu|bunun|bunlar|bundan|onu|onun|ondan|şunu|peki|aynısı|aynısını|devamı)\b")


def _default_deps():
    return {
        "route": router.route,
        "retrieve": retriever.get_top_chunks,
        "calendar": calendar_tool.get_events,
        "mail": mail_tool.get_recent,
        "chat": llm.chat,
        "chat_stream": llm.chat_stream,
        "create_event": calendar_tool.create_event,
        "send_mail": mail_tool.send_mail,
        "open_app": app_launcher.open_app,
    }


def history_block(history):
    """Son turları isteme eklenecek biçimde döndür; geçmiş yoksa boş dize."""
    if not history:
        return ""
    satirlar = [f"{'Kullanıcı' if role == 'user' else 'Asistan'}: {text}"
                for role, text in history[-MAX_HISTORY_TURNS:]]
    return "ÖNCEKİ KONUŞMA:\n" + "\n".join(satirlar) + "\n\n"


def retrieval_query(query, history=None):
    """Takip sorusunu önceki soruyla genişlet; kendi başına anlamlı soruya dokunma."""
    if not history or not _FOLLOW_UP_RE.search(query.lower()):
        return query
    onceki = next((text for role, text in reversed(history) if role == "user"), None)
    return f"{onceki} {query}" if onceki else query


def _result(text, sources=None, pending=None):
    return {"text": text, "sources": sources or [], "pending_action": pending}


def _prepare(query, d, history):
    """Yönlendir ve bağlamı topla.

    ("result", sözlük) → model çağrılmadan biten akış (yazma taslağı, uygulama
    açma, bağlam bulunamaması, araç hatası).
    ("prompt", system, user, kaynaklar) → modele gidecek istem.
    """
    decision = d["route"](query)
    tool, action = decision["tool"], decision["action"]
    gecmis = history_block(history)

    if tool == "app":
        return "result", _open_app_flow(query, d)
    if action == "write":
        return "result", _draft_write(query, tool, d)

    if tool == "documents":
        chunks = d["retrieve"](retrieval_query(query, history))
        if not chunks:
            return "result", _result(NO_INFO)
        context = "\n\n".join(f"[{s}] {t}" for (s, t, _sc) in chunks)
        user = f"{gecmis}BAĞLAM:\n{context}\n\nSORU: {query}"
        return "prompt", SYSTEM_PROMPT, user, [s for (s, _t, _sc) in chunks]

    if tool == "calendar":
        try:
            events = d["calendar"]()
        except Exception as e:
            return "result", _result(f"Takvime şu an ulaşamadım: {e}")
        if not events:
            return "result", _result("Bugün planlanmış bir etkinliğin görünmüyor.", ["Apple Takvim"])
        context = "\n".join(f"- {e['title']} ({e['start']})" for e in events)
        user = (f"{gecmis}Kullanıcının bugünkü takvim etkinlikleri:\n{context}\n\n"
                f"Yalnızca bu listeye dayanarak şu soruyu kısa ve doğru yanıtla: {query}")
        return "prompt", SYSTEM_PROMPT, user, ["Apple Takvim"]

    if tool == "mail":
        try:
            mails = d["mail"]()
        except Exception as e:
            return "result", _result(f"Mail'e şu an ulaşamadım: {e}")
        if not mails:
            return "result", _result("Okunmamış e-postan yok.", ["Apple Mail"])
        context = "\n".join(f"- {m['subject']} — {m['sender']}" for m in mails)
        user = (f"{gecmis}Kullanıcının okunmamış e-postaları:\n{context}\n\n"
                f"Yalnızca bu listeye dayanarak şu soruyu kısa ve doğru yanıtla: {query}")
        return "prompt", SYSTEM_PROMPT, user, ["Apple Mail"]

    return "prompt", SYSTEM_PROMPT, f"{gecmis}{query}", []


def answer(query, deps=None, history=None):
    """Soruyu yanıtla. `history`: [(rol, metin)] — son turlar isteme eklenir."""
    d = deps or _default_deps()
    kind, *payload = _prepare(query, d, history)
    if kind == "result":
        return payload[0]
    system, user, sources = payload
    return _result(d["chat"](system, user), sources)


def answer_stream(query, deps=None, history=None):
    """answer() ile aynı akış; cevabı parça parça verir.

    {"type": "token", "text": …} olayları, en sonda {"type": "final", "result": …}.
    Model çağrılmayan akışlarda yalnızca son olay üretilir.
    """
    d = deps or _default_deps()
    kind, *payload = _prepare(query, d, history)
    if kind == "result":
        yield {"type": "final", "result": payload[0]}
        return
    system, user, sources = payload
    parcalar = []
    for token in d["chat_stream"](system, user):
        parcalar.append(token)
        yield {"type": "token", "text": token}
    yield {"type": "final", "result": _result("".join(parcalar).strip(), sources)}


# --- takvim taslağı: tarih/saat ifadelerini çöz -----------------------------

# Uzun adlar önce denenmeli: "cumartesi" içinde "cuma", "pazartesi" içinde "pazar" var.
WEEKDAYS = ("pazartesi", "salı", "çarşamba", "perşembe", "cuma", "cumartesi", "pazar")
_WEEKDAYS_BY_LENGTH = sorted(enumerate(WEEKDAYS), key=lambda p: -len(p[1]))
MONTHS = ("ocak", "şubat", "mart", "nisan", "mayıs", "haziran",
          "temmuz", "ağustos", "eylül", "ekim", "kasım", "aralık")
DAY_PARTS = (("öğlen", 12, 0), ("sabah", 9, 0), ("öğle", 12, 0), ("akşam", 19, 0))
# Başlıkta bilgi taşımayan emir kipi fiilleri ve dolgu sözcükleri
TITLE_NOISE = ("oluştur", "ekle", "ayarla", "planla", "kur", "lütfen", "günü", "saat")
DEFAULT_HOUR, DEFAULT_MINUTE, DEFAULT_DURATION = 9, 0, 60


def _cut(pattern, text):
    """Eşleşen ifadeyi metinden çıkar (başlığa sızmaması için)."""
    return re.sub(pattern, " ", text, flags=re.IGNORECASE)


def _parse_time(low, rest):
    """(hour, minute, kalan metin) döndür. Saat bulunamazsa varsayılanı kullan."""
    m = re.search(r"\b(\d{1,2})[:.](\d{2})\b", low)
    if m:
        return int(m.group(1)), int(m.group(2)), _cut(r"\b\d{1,2}[:.]\d{2}\b", rest)
    m = re.search(r"\bsaat\s+(\d{1,2})\b", low)
    if m:
        return int(m.group(1)), 0, _cut(r"\bsaat\s+\d{1,2}\b", rest)
    for word, hour, minute in DAY_PARTS:
        if word in low:
            return hour, minute, _cut(word, rest)
    return DEFAULT_HOUR, DEFAULT_MINUTE, rest


def _parse_duration(low, rest):
    m = re.search(r"\b(\d+)\s*saat", low)
    if m:
        return int(m.group(1)) * 60, _cut(r"\b\d+\s*saat\w*", rest)
    m = re.search(r"\b(\d+)\s*dakika", low)
    if m:
        return int(m.group(1)), _cut(r"\b\d+\s*dakika\w*", rest)
    return DEFAULT_DURATION, rest


def _parse_date(low, rest, now, hour, minute):
    """Göreli ve mutlak tarih ifadelerini çöz; tanınmazsa bugüne düş."""
    if "öbür gün" in low or "obur gun" in low:
        return now + timedelta(days=2), _cut(r"öbür gün|obur gun", rest)
    m = re.search(r"\b(\d+)\s*gün\s*sonra\b", low)
    if m:
        return now + timedelta(days=int(m.group(1))), _cut(r"\b\d+\s*gün\s*sonra\b", rest)
    if "haftaya" in low or "gelecek hafta" in low:
        return now + timedelta(days=7), _cut(r"haftaya|gelecek hafta", rest)
    if "yarın" in low:
        return now + timedelta(days=1), _cut(r"yarınki|yarın", rest)
    if "bugün" in low:
        return now, _cut(r"bugünkü|bugün", rest)

    month_re = r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\b"
    m = re.search(month_re, low)
    if m:
        day, month = int(m.group(1)), MONTHS.index(m.group(2)) + 1
        year = now.year if (month, day) >= (now.month, now.day) else now.year + 1
        return now.replace(year=year, month=month, day=day), _cut(month_re, rest)

    for index, name in _WEEKDAYS_BY_LENGTH:
        if name in low:
            ahead = (index - now.weekday()) % 7
            # Aynı gün adı verildiyse ve saat geçmişse gelecek haftaya taşı.
            if ahead == 0 and (hour, minute) <= (now.hour, now.minute):
                ahead = 7
            return now + timedelta(days=ahead), _cut(name + r"\w*", rest)

    return now, rest


def _clean_title(rest):
    for word in TITLE_NOISE:
        rest = re.sub(rf"\b{word}\w*\b", " ", rest, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", rest).strip(" ,.-'\"") or "Etkinlik"


def _parse_calendar_draft(query, now=None):
    """Doğal dildeki isteği taslak etkinliğe çevir. `now` testler için enjekte edilir."""
    now = now or datetime.now()
    low = query.lower()
    hour, minute, rest = _parse_time(low, query)
    duration, rest = _parse_duration(low, rest)
    date, rest = _parse_date(low, rest, now, hour, minute)
    return {
        "type": "calendar", "title": _clean_title(rest),
        "year": date.year, "month": date.month, "day": date.day,
        "hour": hour, "minute": minute, "duration_min": duration,
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
