"""Copy voice interview session JSON into append-only corpus_items."""

from __future__ import annotations



def build_interview_transcript(session: dict) -> str:
    """Plain transcript for display — question line then answer."""

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


def sync_session_to_your_words(
    session: dict,
    *,
    owner_id: str,
    profile_id: str,
    corpus_service: CorpusService | None = None,
    session_id: str | None = None,
    capture_mode: str | None = None,
    **_legacy_kwargs,
) -> int:
    """
    Append answered questions to corpus_items (no interview_answers upsert).
    Returns count of corpus rows inserted.
    """

    if corpus_service is None:
        from services.corpus_service import CorpusService

        service = CorpusService()
    else:
        service = corpus_service
    resolved_session_id = session_id or session.get("id")

    return service.append_from_session(
        session,
        owner_id=owner_id,
        profile_id=profile_id,
        session_id=str(resolved_session_id) if resolved_session_id else None,
        capture_mode=capture_mode,
    )


def backfill_interview_answers_from_sessions(
    *,
    brand_profile_id: str,
    user_id: str,
    sessions: list[dict],
    corpus_service=None,
    **_legacy_kwargs,
) -> bool:
    """
    Legacy hook: migrate empty corpus from old tables / newest session.
    """

    if corpus_service is None:
        from services.corpus_service import CorpusService

        service = CorpusService()
    else:
        service = corpus_service
    if service.backfill_from_legacy_if_empty(brand_profile_id, user_id):
        return True

    for session in sessions:
        if sync_session_to_your_words(
            session,
            owner_id=user_id,
            profile_id=brand_profile_id,
            corpus_service=service,
            session_id=session.get("id"),
        ):
            return True

    return False


def answer_rows_from_session(
    session: dict,
    *,
    owner_id: str,
    profile_id: str,
) -> list[dict]:
    """Kept for tests and typed-answer mapping helpers."""

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
