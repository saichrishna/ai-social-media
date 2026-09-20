"""HTTP client for Brand DNA interview session API (FastAPI source of truth)."""

from __future__ import annotations

import os
from typing import Any

import aiohttp


class BrandDnaBackendClient:
    def __init__(
        self,
        *,
        origin: str | None = None,
        profile_id: str,
        session_id: str,
        user_id: str,
    ) -> None:
        base = (origin or os.getenv("BACKEND_ORIGIN") or "http://127.0.0.1:8000").rstrip(
            "/"
        )
        self._base = base
        self.profile_id = profile_id
        self.session_id = session_id
        self.user_id = user_id

    def _session_url(self, suffix: str = "") -> str:
        root = (
            f"{self._base}/brand-profiles/{self.profile_id}"
            f"/interview-sessions/{self.session_id}{suffix}"
        )
        return f"{root}?user_id={self.user_id}"

    async def get_session(self) -> dict[str, Any]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self._session_url()) as response:
                response.raise_for_status()
                payload = await response.json()
        row = payload.get("interview_session")
        if not row:
            raise RuntimeError("Interview session not found")
        return row

    async def save_answer(
        self,
        *,
        question_key: str,
        answer_text: str,
        source: str = "audio",
    ) -> dict[str, Any]:
        body = {
            "user_id": self.user_id,
            "question_key": question_key,
            "answer_text": answer_text,
            "source": source,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._session_url("/answer"),
                json=body,
            ) as response:
                if response.status >= 400:
                    detail = await response.text()
                    raise RuntimeError(
                        f"save_answer failed ({response.status}): {detail}"
                    )
                return await response.json()

    async def complete(self, transcript: str) -> dict[str, Any]:
        body = {"user_id": self.user_id, "transcript": transcript}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self._session_url("/complete"),
                json=body,
            ) as response:
                response.raise_for_status()
                return await response.json()


def next_unanswered(questions: list[dict[str, Any]]) -> dict[str, Any] | None:
    for question in questions:
        if not question.get("answered"):
            return question
    return None
