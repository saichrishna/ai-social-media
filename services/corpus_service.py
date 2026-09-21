from __future__ import annotations

import re
from typing import Literal

from repositories.corpus_item_repository import CorpusItemRepository
from repositories.interview_answer_repository import InterviewAnswerRepository
from repositories.voice_sample_repository import VoiceSampleRepository
from services.corpus_text import infer_capture_mode, normalize_corpus_text

CorpusSource = Literal[
    "full_talk",
    "mini_talk",
    "paste",
    "type",
    "studio_edit",
    "legacy_transcript",
    "legacy_answer",
]


def corpus_source_for_mode(capture_mode: str) -> CorpusSource:
    if capture_mode == "mini":
        return "mini_talk"
    return "full_talk"


class CorpusService:

    def __init__(self):
        self.repository = CorpusItemRepository()
        self.answer_repository = InterviewAnswerRepository()
        self.sample_repository = VoiceSampleRepository()

    def append_from_session(
        self,
        session: dict,
        *,
        owner_id: str,
        profile_id: str,
        session_id: str | None = None,
        capture_mode: str | None = None,
    ) -> int:

        mode = capture_mode or infer_capture_mode(session)
        source = corpus_source_for_mode(mode)
        rows: list[dict] = []

        for question in session.get("questions") or []:
            content = normalize_corpus_text(
                question.get("answer_text") or "",
            )
            if not content:
                continue
            theme = str(question.get("question_key") or "").strip() or None
            rows.append({
                "user_id": owner_id,
                "brand_profile_id": profile_id,
                "content": content,
                "source": source,
                "theme": theme,
                "question_text": (
                    question.get("question_text") or ""
                ),
                "session_id": session_id,
            })

        if rows:
            self.repository.insert_items(rows)

        return len(rows)

    def append_paste(
        self,
        *,
        owner_id: str,
        profile_id: str,
        content: str,
        source: CorpusSource = "paste",
        theme: str | None = None,
        question_text: str = "",
    ) -> dict | None:

        text = normalize_corpus_text(content)
        if not text:
            return None

        inserted = self.repository.insert_items([{
            "user_id": owner_id,
            "brand_profile_id": profile_id,
            "content": text,
            "source": source,
            "theme": theme,
            "question_text": question_text,
            "session_id": None,
        }])

        return inserted[0] if inserted else None

    def material_count(
        self,
        brand_profile_id: str,
        user_id: str,
    ) -> int:

        return self.repository.count_items(
            brand_profile_id,
            user_id,
        )

    def list_items(
        self,
        brand_profile_id: str,
        user_id: str,
    ):

        return self.repository.list_items(
            brand_profile_id,
            user_id,
        )

    def backfill_from_legacy_if_empty(
        self,
        brand_profile_id: str,
        user_id: str,
    ) -> bool:

        if self.material_count(brand_profile_id, user_id) > 0:
            return False

        existing_texts: set[str] = set()
        rows: list[dict] = []

        answers = self.answer_repository.get_answers(
            brand_profile_id,
            user_id,
        )

        for answer in answers:
            content = normalize_corpus_text(
                answer.get("answer_text") or "",
            )
            if not content or content in existing_texts:
                continue
            existing_texts.add(content)
            rows.append({
                "user_id": user_id,
                "brand_profile_id": brand_profile_id,
                "content": content,
                "source": "legacy_answer",
                "theme": answer.get("question_key"),
                "question_text": answer.get("question_text") or "",
                "session_id": None,
            })

        samples = self.sample_repository.get_samples(
            brand_profile_id,
            user_id,
        )

        for sample in samples:
            content = normalize_corpus_text(
                sample.get("content") or "",
            )
            if not content:
                continue
            if content in existing_texts:
                continue
            if any(
                content in other or other in content
                for other in existing_texts
                if len(other) > 80 and len(content) > 80
            ):
                continue
            existing_texts.add(content)
            sample_source = sample.get("source") or "paste"
            mapped: CorpusSource = (
                "paste"
                if sample_source == "paste"
                else "legacy_transcript"
            )
            rows.append({
                "user_id": user_id,
                "brand_profile_id": brand_profile_id,
                "content": content,
                "source": mapped,
                "theme": None,
                "question_text": "",
                "session_id": None,
            })

        if rows:
            self.repository.insert_items(rows)
            return True

        return False

    def select_chunks_for_generation(
        self,
        brand_profile_id: str,
        user_id: str,
        *,
        topic: str = "",
        limit: int = 12,
    ) -> list[str]:

        items = self.repository.list_items(
            brand_profile_id,
            user_id,
        )

        if not items:
            return []

        topic_tokens = {
            token
            for token in re.split(r"\W+", topic.lower())
            if len(token) > 2
        }

        scored: list[tuple[int, str, str]] = []

        for item in items:
            content = normalize_corpus_text(item.get("content") or "")
            if not content:
                continue
            created = str(item.get("created_at") or "")
            score = 0
            if topic_tokens:
                lower = content.lower()
                score = sum(1 for token in topic_tokens if token in lower)
            scored.append((score, created, content))

        scored.sort(key=lambda row: (row[0], row[1]), reverse=True)

        selected: list[str] = []
        seen: set[str] = set()

        for score, _created, content in scored:
            if score > 0 and content not in seen:
                selected.append(content)
                seen.add(content)
            if len(selected) >= max(8, limit - 4):
                break

        for score, _created, content in scored:
            if content in seen:
                continue
            selected.append(content)
            seen.add(content)
            if len(selected) >= limit:
                break

        return selected[:limit]
