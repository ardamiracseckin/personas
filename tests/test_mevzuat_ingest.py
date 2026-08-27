"""Kanun PDF'lerinin bilgi tabanına yüklenmesi.

Atıf parçanın ilk satırına yazılır. Sebebi şu: modele giden bağlamda madde
numarası yoksa model onu uyduramaz, uydurursa da yanlış uydurur. Atıf metnin
içinde olursa hem model doğru maddeyi söyler hem kullanıcı kaynak panelinde
görür — şema değişikliği gerekmeden.
"""
from app import ingest, mevzuat, store

KANUN = """İŞ KANUNU
Kanun Numarası : 4857
Kabul Tarihi : 22/5/2003

Süreli fesih
Madde 17 - Belirsiz süreli iş sözleşmelerinin feshinden önce bildirim gerekir.

Kıdem tazminatı
Madde 120 - Kıdem tazminatına ilişkin hüküm.
"""


def test_citation_is_the_first_line_of_every_chunk():
    parcalar = ingest.mevzuat_parcalari(KANUN, kaynak="4857 İş Kanunu")
    ilk = parcalar[0]["text"].splitlines()[0]
    assert "4857" in ilk and "md. 17" in ilk


def test_article_heading_is_kept_next_to_the_citation():
    parcalar = ingest.mevzuat_parcalari(KANUN, kaynak="4857 İş Kanunu")
    assert "Süreli fesih" in parcalar[0]["text"].splitlines()[0]


def test_article_text_stays_verbatim_below_the_citation():
    parcalar = ingest.mevzuat_parcalari(KANUN, kaynak="4857 İş Kanunu")
    assert "Belirsiz süreli iş sözleşmelerinin feshinden önce bildirim gerekir." \
        in parcalar[0]["text"]


def test_source_is_the_law_not_the_article():
    # Arayüzdeki belge listesi 8 kanunla sınırlı kalsın; her madde ayrı belge
    # gibi görünürse liste 2500 satır olur.
    parcalar = ingest.mevzuat_parcalari(KANUN, kaynak="4857 İş Kanunu")
    assert {p["source"] for p in parcalar} == {"4857 İş Kanunu"}


def test_every_article_produces_at_least_one_chunk():
    parcalar = ingest.mevzuat_parcalari(KANUN, kaynak="4857 İş Kanunu")
    maddeler = {p["madde"] for p in parcalar}
    assert maddeler == {"17", "120"}


def test_ingesting_a_law_replaces_its_previous_chunks(tmp_path, monkeypatch):
    from app import config
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    store.init_db()
    sahte = lambda metinler: [[float(len(m))] for m in metinler]
    ingest.ingest_mevzuat_text(KANUN, kaynak="4857 İş Kanunu", embed_fn=sahte)
    ilk = dict(store.sources())["4857 İş Kanunu"]
    ingest.ingest_mevzuat_text(KANUN, kaynak="4857 İş Kanunu", embed_fn=sahte)
    assert dict(store.sources())["4857 İş Kanunu"] == ilk
