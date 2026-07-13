import re

def parse_raw_file(filepath):
    """
    Splits a raw text file into chunks, each tagged with its legal source.
    Sections are marked with a line: ### SOURCE: <name>
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split the file right before each "### SOURCE:" marker
    sections = re.split(r"(?=^### SOURCE:)", content, flags=re.MULTILINE)

    chunks = []
    for section in sections:
        section = section.strip()
        if not section:
            continue

        header_match = re.match(r"### SOURCE:\s*(.+)", section)
        if not header_match:
            continue

        source_name = header_match.group(1).strip()
        body = section[header_match.end():].strip()

        # If a provision is long, split it into paragraph-level chunks
        paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
        for para in paragraphs:
            chunks.append({"source_name": source_name, "chunk_text": para})

    return chunks


if __name__ == "__main__":
    # Quick manual test — run this file directly to sanity-check parsing
    chunks = parse_raw_file("data/raw/termination_law.txt")
    print(f"Parsed {len(chunks)} chunks:\n")
    for c in chunks:
        print(f"[{c['source_name']}] {c['chunk_text'][:80]}...")