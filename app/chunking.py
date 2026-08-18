def _is_heading(para):
    return para.lstrip().startswith("#")


def chunk_text(text, max_chars=800):
    """Split text into chunks on blank lines, greedily packing up to max_chars.

    Markdown başlıkları parça sınırı sayılır ve her parçanın başına kendi başlığı
    yazılır; böylece parça hangi konuya ait olduğunu tek başına taşır (küçük model
    için bağlam, kullanıcı için kaynak netliği).
    """
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, body, heading = [], [], ""

    def flush():
        if body:
            chunks.append("\n\n".join(([heading] if heading else []) + body))
            body.clear()

    for para in paras:
        if _is_heading(para):
            flush()
            heading = para.splitlines()[0].strip()
            continue
        candidate = "\n\n".join(([heading] if heading else []) + body + [para])
        if body and len(candidate) > max_chars:
            flush()
        body.append(para)
    flush()
    return chunks
