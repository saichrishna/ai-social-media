from unittest.mock import MagicMock

from services.interview_session_sync import (
    answer_rows_from_session,
    backfill_interview_answers_from_sessions,
    build_interview_transcript,
    sync_session_to_your_words,
)


def test_build_interview_transcript_includes_cold_open_and_qa():
    session = {
        "transcript": "coldpress quality oil\nextra line ignored for cold",
        "questions": [
            {
                "question_text": "What mistakes?",
                "answer_text": "Too much oil.",
                "answered": True,
            }
        ],
    }
    text = build_interview_transcript(session)
    assert "coldpress quality oil" in text
    assert "What mistakes?" in text
    assert "Too much oil." in text


def test_answer_rows_from_session_skips_empty():
    session = {
        "questions": [
            {
                "question_key": "a",
                "question_text": "Q1",
                "answer_text": "  yes ",
                "source": "audio",
            },
            {
                "question_key": "b",
                "question_text": "Q2",
                "answer_text": "",
            },
        ]
    }
    rows = answer_rows_from_session(
        session,
        owner_id="user-1",
        profile_id="brand-1",
    )
    assert len(rows) == 1
    assert rows[0]["question_key"] == "a"
    assert rows[0]["answer_text"] == "yes"


def test_backfill_runs_when_corpus_empty():
    corpus = MagicMock()
    corpus.backfill_from_legacy_if_empty.return_value = False
    corpus.append_from_session.return_value = 1

    session = {
        "questions": [
            {
                "question_key": "customers_get_wrong",
                "question_text": "Mistakes?",
                "answer_text": "Uses too much.",
                "source": "audio",
            }
        ],
        "transcript": "cold open",
    }

    ran = backfill_interview_answers_from_sessions(
        brand_profile_id="brand-1",
        user_id="user-1",
        sessions=[session],
        corpus_service=corpus,
    )

    assert ran is True
    corpus.append_from_session.assert_called()


def test_sync_session_appends_corpus():
    corpus = MagicMock()
    corpus.append_from_session.return_value = 1
    session = {
        "transcript": "hello",
        "questions": [
            {
                "question_key": "k1",
                "question_text": "Q",
                "answer_text": "A",
                "source": "type",
            }
        ],
    }
    count = sync_session_to_your_words(
        session,
        owner_id="u",
        profile_id="b",
        corpus_service=corpus,
        session_id="sess-1",
        capture_mode="mini",
    )
    assert count == 1
    corpus.append_from_session.assert_called_once()
