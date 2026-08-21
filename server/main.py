"""personas HTTP sunucusu.

İş mantığı `app/` içindedir; burası yalnızca onu HTTP'ye açar. Cevaplar SSE ile
akıtılır: arayüz ilk kelimeleri saniyenin altında gösterebilsin diye.
"""
import json
import re
import shutil
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import assistant, chat_store, config, ingest, llm, models, store

STATIC_DIR = Path(__file__).resolve().parent / "static"
TITLE_PROMPT = (
    "Aşağıdaki soruya 2-4 kelimelik, tırnaksız ve noktasız bir başlık yaz. "
    "Yalnızca başlığı yaz, başka hiçbir şey yazma."
)

@asynccontextmanager
async def lifespan(_app):
    store.init_db()
    chat_store.init_db()
    # Modeli arka planda ısıt: Foundry hareketsizlikte modeli bellekten atıyor ve
    # ilk soru ~30 saniye sürüyordu. Sunucu açılışı bunu beklemesin diye ayrı iş parçacığı.
    threading.Thread(target=models.ensure_loaded, daemon=True).start()
    yield


app = FastAPI(title="personas", lifespan=lifespan)


# ----------------------------------------------------------------- yardımcılar

def _sse(payload):
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _require_conversation(conversation_id):
    if not any(c["id"] == conversation_id for c in chat_store.list_conversations()):
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı.")


def clean_title(raw, fallback):
    """Model başlığını kullanılabilir hâle getir; saçmalarsa sorunun kendisine düş."""
    baslik = (raw or "").splitlines()[0] if raw else ""
    baslik = re.sub(r"[\"'`*#|]+", " ", baslik)          # tırnak, madde imi, boru işareti
    baslik = re.sub(r"^\s*(başlık|title)\s*[:\-]\s*", "", baslik, flags=re.IGNORECASE)
    baslik = re.sub(r"\s{2,}", " ", baslik).strip(" .,:;-")
    kelimeler = baslik.split()
    if not (1 <= len(kelimeler) <= 6):                  # tek kelimeden kısa ya da cümle gibiyse
        baslik = ""
    return (baslik or fallback)[:60]


def generate_title(first_message):
    """İlk sorudan kısa bir sohbet başlığı üret; başarısız olursa sorunun kendisi."""
    try:
        ham = llm.chat(TITLE_PROMPT, first_message)
    except Exception:
        ham = ""
    return clean_title(ham, first_message)


# ------------------------------------------------------------------- konuşmalar

class ConversationIn(BaseModel):
    title: str | None = None


@app.get("/api/conversations")
def list_conversations():
    return chat_store.list_conversations()


@app.post("/api/conversations")
def create_conversation(body: ConversationIn):
    yeni = chat_store.create_conversation(body.title)
    return {"id": yeni, "title": body.title or chat_store.DEFAULT_TITLE}


@app.patch("/api/conversations/{conversation_id}")
def rename_conversation(conversation_id: int, body: ConversationIn):
    _require_conversation(conversation_id)
    chat_store.rename_conversation(conversation_id, body.title or chat_store.DEFAULT_TITLE)
    return {"ok": True}


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int):
    chat_store.delete_conversation(conversation_id)
    return {"ok": True}


@app.get("/api/conversations/{conversation_id}/messages")
def get_messages(conversation_id: int):
    _require_conversation(conversation_id)
    return chat_store.get_messages(conversation_id)


# ------------------------------------------------------------------ sohbet akışı

class ChatIn(BaseModel):
    conversation_id: int
    message: str | None = None
    regenerate: bool = False
    edit_message_id: int | None = None


def _last_user_message(conversation_id):
    for mesaj in reversed(chat_store.get_messages(conversation_id)):
        if mesaj["role"] == "user":
            return mesaj
    return None


def _chat_events(conversation_id, message, ilk_mesaj_mi):
    """Token → final → (gerekiyorsa) başlık olaylarını üret."""
    gecmis = chat_store.history(conversation_id)
    kullanici_id = chat_store.add_message(conversation_id, "user", message)
    try:
        for olay in assistant.answer_stream(message, history=gecmis):
            if olay["type"] == "token":
                yield _sse(olay)
            else:
                sonuc = olay["result"]
                chat_store.add_message(conversation_id, "assistant", sonuc["text"],
                                       sonuc["sources"], sonuc.get("chunks"))
                yield _sse({"type": "final", "result": sonuc, "user_message_id": kullanici_id})
    except Exception as e:  # model kapalı, servis erişilemez vb.
        yield _sse({"type": "error", "message": str(e)})
        return

    if ilk_mesaj_mi:
        baslik = generate_title(message)
        chat_store.rename_conversation(conversation_id, baslik)
        yield _sse({"type": "title", "title": baslik})


@app.post("/api/chat")
def chat(body: ChatIn):
    _require_conversation(body.conversation_id)

    if body.edit_message_id:
        # Düzenlenen mesaj ve sonrasındaki her şey silinir; yeni metinle baştan sorulur.
        chat_store.delete_messages_after(body.conversation_id, body.edit_message_id)
        mesaj = (body.message or "").strip()
        if not mesaj:
            raise HTTPException(status_code=400, detail="Boş mesaj gönderilemez.")
    elif body.regenerate:
        # Son cevabı at, son soruyu yeniden sor.
        son_soru = _last_user_message(body.conversation_id)
        if not son_soru:
            raise HTTPException(status_code=400, detail="Yeniden üretilecek bir soru yok.")
        chat_store.delete_messages_after(body.conversation_id, son_soru["id"])
        mesaj = son_soru["text"]
    else:
        mesaj = (body.message or "").strip()
        if not mesaj:
            raise HTTPException(status_code=400, detail="Boş mesaj gönderilemez.")

    ilk_mesaj_mi = not chat_store.get_messages(body.conversation_id)
    return StreamingResponse(
        _chat_events(body.conversation_id, mesaj, ilk_mesaj_mi),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ConfirmIn(BaseModel):
    conversation_id: int
    pending_action: dict


@app.post("/api/confirm")
def confirm(body: ConfirmIn):
    _require_conversation(body.conversation_id)
    try:
        mesaj = assistant.confirm(body.pending_action)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"İşlem tamamlanamadı: {e}")
    chat_store.add_message(body.conversation_id, "assistant", mesaj)
    return {"message": mesaj}


# --------------------------------------------------------------------- belgeler

@app.get("/api/documents")
def list_documents():
    return [{"name": ad, "chunks": sayi} for (ad, sayi) in store.sources()]


@app.post("/api/documents")
def upload_document(file: UploadFile):
    ad = Path(file.filename or "").name
    if Path(ad).suffix.lower() not in ingest.SUPPORTED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Yalnızca {', '.join(ingest.SUPPORTED_SUFFIXES)} dosyaları yüklenebilir.")

    config.DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    hedef = config.DOCUMENTS_DIR / ad
    with hedef.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        parca = ingest.ingest_file(hedef)
    except Exception as e:
        hedef.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Belge işlenemedi: {e}")
    return {"name": ad, "chunks": parca}


@app.delete("/api/documents/{name}")
def delete_document(name: str):
    ad = Path(name).name
    store.delete_by_source(ad)
    (config.DOCUMENTS_DIR / ad).unlink(missing_ok=True)
    return {"ok": True}


# --------------------------------------------------------------------- modeller

class ModelIn(BaseModel):
    alias: str


@app.get("/api/status")
def status():
    """Arayüzün model durumunu gösterebilmesi için: hangi model, bellekte mi."""
    return {"model": models.current(), "loaded": models.is_loaded()}


@app.get("/api/models")
def list_models():
    return models.catalog()


@app.post("/api/models")
def switch_model(body: ModelIn):
    try:
        secilen = models.switch(body.alias)
    except (ValueError, RuntimeError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"alias": secilen}


# ---------------------------------------------------------------------- arayüz

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
