"""Copy voice interview session JSON into durable Your words tables."""

from __future__ import annotations

from repositories.interview_answer_repository import InterviewAnswerRepository
from repositories.voice_sample_repository import VoiceSampleRepository


def build_interview_transcript(session: dict) -> str:
    """Plain transcript for samples — question line then answer, no internal keys."""

    parts: list[str] = []
    cold = (session.get("transcript") or "").strip().split("\n")[0].strip()
    if cold:
        parts.append(cold)

    for question in session.get("questions") or []:
        answer = (question.get("answer_text") or "").strip()
        if not answer:
            continue
        label = (question.get("question_text") or "").strip()
        if label:
            parts.append(f"{label}\n{answer}")
        else:
            parts.append(answer)

    return "\n\n".join(parts).strip()


def answer_rows_from_session(
    session: dict,
    *,
    owner_id: str,
    profile_id: str,
) -> list[dict]:
    rows: list[dict] = []

    for question in session.get("questions") or []:
        answer_text = (question.get("answer_text") or "").strip()
        if not answer_text:
            continue
        source = question.get("source") or "type"
        if source not in {"type", "audio"}:
            source = "type"
        question_key = question.get("question_key")
        if not question_key:
            continue
        rows.append(
            {
                "user_id": owner_id,
                "brand_profile_id": profile_id,
                "question_key": question_key,
                "question_text": question.get("question_text") or "",
                "answer_text": answer_text,
                "source": source,
            }
        )

    return rows


def sync_session_to_your_words(
    session: dict,
    *,
    owner_id: str,
    profile_id: str,
    answer_repository: InterviewAnswerRepository,
    sample_repository: VoiceSampleRepository | None = None,
    transcript: str | None = None,
    include_voice_sample: bool = True,
) -> int:
    """
    Upsert per-question rows into interview_answers and optionally append
    a combined transcript voice sample. Returns count of answer rows synced.
    """

    rows = answer_rows_from_session(
        session,
        owner_id=owner_id,
        profile_id=profile_id,
    )

    if rows:
        answer_repository.upsert_answers(rows)

    if include_voice_sample and sample_repository is not None:
        merged = (
            (transcript or "").strip()
            or build_interview_transcript(session)
            or (session.get("transcript") or "").strip()
        ).strip()
        if merged:
            sample_repository.create_sample(
                {
                    "user_id": owner_id,
                    "brand_profile_id": profile_id,
                    "source": "audio",
                    "content": merged,
                }
            )

    return len(rows)


def backfill_interview_answers_from_sessions(
    *,
    brand_profile_id: str,
    user_id: str,
    sessions: list[dict],
    answer_repository: InterviewAnswerRepository,
    sample_repository: VoiceSampleRepository | None = None,
) -> bool:
    """
    If interview_answers is empty, copy from the newest session that has
    at least one answered question. Returns True when a sync ran.
    """

    existing = answer_repository.get_answers(
        brand_profile_id=brand_profile_id,
        user_id=user_id,
    )
    if existing:
        return False

    for session in sessions:
        if not answer_rows_from_session(
            session,
            owner_id=user_id,
            profile_id=brand_profile_id,
        ):
            continue
        sync_session_to_your_words(
            session,
            owner_id=user_id,
            profile_id=brand_profile_id,
            answer_repository=answer_repository,
            sample_repository=sample_repository,
            include_voice_sample=True,
        )
        return True

    return False
