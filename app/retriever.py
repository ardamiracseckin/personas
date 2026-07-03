from app import config, llm, store
from app.similarity import cosine


def get_top_chunks(query, k=None, embed_fn=None):
    """Return up to k (source, text, score) chunks most similar to query, above threshold."""
    k = k or config.TOP_K
    embed_fn = embed_fn or llm.embed
    qvec = embed_fn([query])[0]
    scored = [(src, txt, cosine(qvec, emb)) for (src, txt, emb) in store.all_chunks()]
    scored = [row for row in scored if row[2] >= config.SIM_THRESHOLD]
    scored.sort(key=lambda r: r[2], reverse=True)
    return scored[:k]
