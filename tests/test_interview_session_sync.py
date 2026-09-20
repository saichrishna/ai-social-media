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


def test_backfill_runs_when_answers_empty():
    answers = MagicMock()
    answers.get_answers.side_effect = [[], [{"question_key": "a"}]]
    samples = MagicMock()

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
        answer_repository=answers,
        sample_repository=samples,
    )

    assert ran is True
    answers.upsert_answers.assert_called_once()
    samples.create_sample.assert_called_once()


def test_sync_session_upserts_and_sample():
    answers = MagicMock()
    samples = MagicMock()
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
        answer_repository=answers,
        sample_repository=samples,
        transcript="hello\n\nQ\nA",
    )
    assert count == 1
    answers.upsert_answers.assert_called_once()
    samples.create_sample.assert_called_once()
