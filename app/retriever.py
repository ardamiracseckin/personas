from app import config, lexical, llm, store
from app.similarity import cosine


def score(query, text, qvec, embedding):
    """Hibrit skor: anlam (kosinüs) + yazım hatasına dayanıklı sözlüksel eşleşme."""
    return (config.DENSE_WEIGHT * cosine(qvec, embedding)
            + config.LEXICAL_WEIGHT * lexical.fuzzy_score(query, text))


def accepts(total, dense, lex, threshold=None):
    """Parça bağlama alınsın mı: eşiği geçiyor ya da kelime eşleşmesi güçlü."""
    if total >= (config.SIM_THRESHOLD if threshold is None else threshold):
        return True
    return lex >= config.LEXICAL_RESCUE and dense >= config.DENSE_FLOOR


# Sözlüksel katmanın uygulanacağı aday sayısı. Kosinüs bütün parçalar üzerinde
# ucuzdur (3.069 parçada 0,08 sn); SequenceMatcher tabanlı sözlüksel eşleşme
# pahalıdır (aynı korpusta 8,7 sn). Yazım hatası toleransı yalnızca en yakın
# adaylarda gerekli olduğu için sözlüksel katman havuzla sınırlanır.
ADAY_HAVUZU = 60


def get_top_chunks(query, k=None, embed_fn=None):
    """Return up to k (source, text, score) chunks most similar to query, above threshold."""
    k = k or config.TOP_K
    embed_fn = embed_fn or llm.embed
    qvec = embed_fn([query])[0]

    # 1) Ucuz katman: bütün parçalarda kosinüs.
    yogun = [(cosine(qvec, emb), src, txt) for (src, txt, emb) in store.all_chunks()]
    yogun.sort(key=lambda r: r[0], reverse=True)

    # 2) Pahalı katman: yalnız en yakın adaylarda sözlüksel eşleşme.
    scored = []
    for dense, src, txt in yogun[:ADAY_HAVUZU]:
        lex = lexical.fuzzy_score(query, txt)
        total = config.DENSE_WEIGHT * dense + config.LEXICAL_WEIGHT * lex
        if accepts(total, dense, lex):
            scored.append((src, txt, total))
    scored.sort(key=lambda r: r[2], reverse=True)
    return scored[:k]
