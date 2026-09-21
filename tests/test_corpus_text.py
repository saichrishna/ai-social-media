from services.corpus_text import infer_capture_mode, normalize_corpus_text


def test_infer_capture_mode_mini_from_two_questions():
    session = {
        "questions": [
            {"question_key": "unpublished_advice"},
            {"question_key": "customer_sentence"},
        ],
    }
    assert infer_capture_mode(session) == "mini"


def test_normalize_corpus_text_collapses_whitespace():
    assert normalize_corpus_text("  hello \n world  ") == "hello world"
