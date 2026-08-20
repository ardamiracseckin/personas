from app import config, lexical, llm, store
from app.similarity import cosine


def score(query, text, qvec, embedding):
    """Hibrit skor: anlam (kosinüs) + yazım hatasına dayanıklı sözlüksel eşleşme."""
    return (config.DENSE_WEIGHT * cosine(qvec, embedding)
            + config.LEXICAL_WEIGHT * lexical.fuzzy_score(query, text))


def get_top_chunks(query, k=None, embed_fn=None):
    """Return up to k (source, text, score) chunks most similar to query, above threshold."""
    k = k or config.TOP_K
    embed_fn = embed_fn or llm.embed
    qvec = embed_fn([query])[0]
    scored = [(src, txt, score(query, txt, qvec, emb)) for (src, txt, emb) in store.all_chunks()]
    scored = [row for row in scored if row[2] >= config.SIM_THRESHOLD]
    scored.sort(key=lambda r: r[2], reverse=True)
    return scored[:k]
