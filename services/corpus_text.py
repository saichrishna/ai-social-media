import re

MINI_TALK_KEYS = frozenset({"unpublished_advice", "customer_sentence"})


def normalize_corpus_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def infer_capture_mode(session: dict) -> str:
    mode = str(session.get("capture_mode") or "").strip().lower()
    if mode in {"full", "mini"}:
        return mode
    questions = session.get("questions") or []
    if len(questions) == 2:
        keys = {
            str(question.get("question_key") or "").strip()
            for question in questions
        }
        if keys <= MINI_TALK_KEYS and keys:
            return "mini"
    return "full"
