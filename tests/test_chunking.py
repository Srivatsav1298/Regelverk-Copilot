import pytest
from data.chunk import parse_raw_file

def test_single_provision(tmpdir):
    # Create a temporary file with a single provision
    content = """
### SOURCE: Test Law § 1
This is the only paragraph.
"""
    filepath = tmpdir.join("test.txt")
    filepath.write(content)
    chunks = parse_raw_file(str(filepath))
    assert len(chunks) == 1
    assert chunks[0]["source_name"] == "Test Law § 1"
    assert chunks[0]["chunk_text"] == "This is the only paragraph."

def test_multiple_provisions(tmpdir):
    content = """
### SOURCE: Test Law § 1
First provision.

### SOURCE: Test Law § 2
Second provision.
"""
    filepath = tmpdir.join("test.txt")
    filepath.write(content)
    chunks = parse_raw_file(str(filepath))
    assert len(chunks) == 2
    assert chunks[0]["source_name"] == "Test Law § 1"
    assert chunks[0]["chunk_text"] == "First provision."
    assert chunks[1]["source_name"] == "Test Law § 2"
    assert chunks[1]["chunk_text"] == "Second provision."

def test_multi_paragraph_splitting(tmpdir):
    content = """
### SOURCE: Test Law § 1
First paragraph.

Second paragraph.

Third paragraph.
"""
    filepath = tmpdir.join("test.txt")
    filepath.write(content)
    chunks = parse_raw_file(str(filepath))
    assert len(chunks) == 3
    assert chunks[0]["source_name"] == "Test Law § 1"
    assert chunks[0]["chunk_text"] == "First paragraph."
    assert chunks[1]["source_name"] == "Test Law § 1"
    assert chunks[1]["chunk_text"] == "Second paragraph."
    assert chunks[2]["source_name"] == "Test Law § 1"
    assert chunks[2]["chunk_text"] == "Third paragraph."

def test_ignoring_preamble(tmpdir):
    content = """
This is preamble text that should be ignored.
More preamble.

### SOURCE: Test Law § 1
This is the first real chunk.

### SOURCE: Test Law § 2
Second chunk.
"""
    filepath = tmpdir.join("test.txt")
    filepath.write(content)
    chunks = parse_raw_file(str(filepath))
    assert len(chunks) == 2
    assert chunks[0]["source_name"] == "Test Law § 1"
    assert chunks[0]["chunk_text"] == "This is the first real chunk."
    assert chunks[1]["source_name"] == "Test Law § 2"
    assert chunks[1]["chunk_text"] == "Second chunk."

def test_empty_file(tmpdir):
    content = ""
    filepath = tmpdir.join("test.txt")
    filepath.write(content)
    chunks = parse_raw_file(str(filepath))
    assert chunks == []