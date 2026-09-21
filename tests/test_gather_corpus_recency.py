def test_gather_corpus_entry_sorting():

    entries = [
        ("old sample", "2020-01-01T00:00:00Z"),
        ("new sample", "2026-01-01T00:00:00Z"),
    ]
    entries.sort(key=lambda item: item[1], reverse=True)
    corpus = [text for text, _timestamp in entries]

    assert corpus[0] == "new sample"
    assert corpus[1] == "old sample"
