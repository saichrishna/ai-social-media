"""Stream STT for the active question; UI saves answers (no auto-advance on VAD)."""

from __future__ import annotations

from typing import Any

from loguru import logger

from pipecat.frames.frames import (
    ClientConnectedFrame,
    Frame,
    InputTransportMessageFrame,
    InterimTranscriptionFrame,
    OutputTransportMessageFrame,
    StartFrame,
    TranscriptionFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from voice_agent.backend_client import BrandDnaBackendClient, next_unanswered


class BrandInterviewProcessor(FrameProcessor):
    """Announces session questions and relays one combined transcript per question."""

    def __init__(
        self,
        *,
        backend: BrandDnaBackendClient,
        read_questions_aloud: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._backend = backend
        self._read_questions_aloud = read_questions_aloud
        self._started = False
        self._current_key: str | None = None
        self._segments: list[str] = []

    async def _emit(self, message: dict[str, Any]) -> None:
        await self.push_frame(
            OutputTransportMessageFrame(message=message),
            FrameDirection.DOWNSTREAM,
        )

    async def _announce_current_question(self, session: dict[str, Any]) -> None:
        if session.get("status") != "in_progress":
            await self._emit(
                {
                    "type": "session_closed",
                    "message": (
                        "This interview is already finished. "
                        "Use Start new sitting to begin again."
                    ),
                }
            )
            return

        current = next_unanswered(session.get("questions") or [])
        if not current:
            await self._emit({"type": "all_questions_answered"})
            return

        self._current_key = current.get("question_key")
        self._segments = []
        await self._emit(
            {
                "type": "question",
                "question_key": self._current_key,
                "question_text": current.get("question_text") or "",
                "prep_brief": session.get("prep_brief") or "",
                "read_aloud": self._read_questions_aloud,
            }
        )

    async def _emit_question_transcript(self) -> None:
        if not self._current_key:
            return
        text = " ".join(part.strip() for part in self._segments if part.strip()).strip()
        await self._emit(
            {
                "type": "question_transcript",
                "question_key": self._current_key,
                "text": text,
            }
        )

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, StartFrame):
            self._started = True
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, ClientConnectedFrame) and self._started:
            try:
                session = await self._backend.get_session()
                await self._announce_current_question(session)
            except Exception as error:
                logger.exception("Failed to load interview session")
                await self._emit({"type": "error", "message": str(error)})
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, InterimTranscriptionFrame):
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, TranscriptionFrame):
            text = (frame.text or "").strip()
            if text and self._current_key:
                self._segments.append(text)
                await self._emit_question_transcript()
            await self.push_frame(frame, direction)
            return

        if isinstance(frame, InputTransportMessageFrame):
            message = frame.message
            if isinstance(message, dict) and message.get("type") == "sync_question":
                key = str(message.get("question_key") or "").strip()
                if key:
                    self._current_key = key
                    self._segments = []
                    await self._emit(
                        {
                            "type": "question_transcript",
                            "question_key": key,
                            "text": "",
                        }
                    )
            await self.push_frame(frame, direction)
            return

        await self.push_frame(frame, direction)
