def verify_citations(citations: list, retrieved_chunks: list) -> list:
    """
    Checks that each cited excerpt is an actual substring of a retrieved
    chunk's stored text. Matches source_name by prefix rather than exact
    equality, since the model sometimes truncates the full source name
    (e.g. drops the "| Title" suffix) while still meaning the same chunk.
    """
    verified = []
    for citation in citations:
        # Find the retrieved chunk whose source_name STARTS WITH the model's
        # (possibly truncated) citation source_name — not exact match.
        matching_chunk = next(
            (c for c in retrieved_chunks
             if c["source_name"].startswith(citation.source_name)),
            None
        )

        if matching_chunk is None:
            is_verified = False
        else:
            normalized_source = " ".join(matching_chunk["chunk_text"].split())
            normalized_excerpt = " ".join(citation.excerpt.split())
            is_verified = normalized_excerpt in normalized_source

        verified.append({"citation": citation, "verified": is_verified})

        if not is_verified:
            print(f"⚠️  UNVERIFIED CITATION: '{citation.excerpt[:80]}...' "
                  f"source_name='{citation.source_name}'")

    return verified