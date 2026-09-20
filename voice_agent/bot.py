"""Pipecat Small WebRTC sidecar for Brand DNA interview (Slice B).

Run from repo root::

    python voice_agent/bot.py -t webrtc --port 8765

Connect from the UI with ``NEXT_PUBLIC_PIPECAT_URL`` pointing at this server.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from loguru import logger

load_dotenv(ROOT / ".env")

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.runner.types import RunnerArguments, SmallWebRTCRunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.whisper.stt import Model, WhisperSTTService
from pipecat.transports.base_transport import TransportParams
from pipecat.workers.runner import WorkerRunner

from voice_agent.backend_client import BrandDnaBackendClient
from voice_agent.interview_processor import BrandInterviewProcessor


def _session_config(body: dict | None) -> dict:
    data = dict(body or {})
    if not data.get("profile_id") and isinstance(data.get("request_data"), dict):
        data = {**data, **data["request_data"]}
    if not data.get("profile_id") and isinstance(data.get("requestData"), dict):
        data = {**data, **data["requestData"]}
    profile_id = (data.get("profile_id") or data.get("profileId") or "").strip()
    session_id = (data.get("session_id") or data.get("sessionId") or "").strip()
    user_id = (data.get("user_id") or data.get("userId") or "").strip()
    backend_origin = (
        data.get("backend_origin")
        or data.get("backendOrigin")
        or os.getenv("BACKEND_ORIGIN")
        or "http://127.0.0.1:8000"
    )
    read_aloud = bool(
        data.get("read_questions_aloud") or data.get("readQuestionsAloud")
    )
    missing = [
        name
        for name, value in [
            ("profile_id", profile_id),
            ("session_id", session_id),
            ("user_id", user_id),
        ]
        if not value
    ]
    if missing:
        raise ValueError(
            f"WebRTC requestData missing: {', '.join(missing)}"
        )
    return {
        "profile_id": profile_id,
        "session_id": session_id,
        "user_id": user_id,
        "backend_origin": backend_origin,
        "read_questions_aloud": read_aloud,
    }


async def bot(runner_args: RunnerArguments) -> None:
    if not isinstance(runner_args, SmallWebRTCRunnerArguments):
        logger.error("Brand DNA voice sidecar supports Small WebRTC only")
        return

    try:
        cfg = _session_config(runner_args.body)
    except ValueError as error:
        logger.error(str(error))
        return

    backend = BrandDnaBackendClient(
        origin=cfg["backend_origin"],
        profile_id=cfg["profile_id"],
        session_id=cfg["session_id"],
        user_id=cfg["user_id"],
    )

    whisper_model = os.getenv("WHISPER_MODEL_SIZE", "base")
    whisper_device = os.getenv("WHISPER_DEVICE", "cpu")
    whisper_compute = os.getenv("WHISPER_COMPUTE_TYPE", "int8")

    transport_params = {
        "webrtc": lambda: TransportParams(
            audio_in_enabled=True,
            audio_out_enabled=cfg["read_questions_aloud"],
        ),
    }

    transport = await create_transport(runner_args, transport_params)
    vad = VADProcessor(vad_analyzer=SileroVADAnalyzer())
    try:
        whisper = Model(whisper_model)
    except ValueError:
        whisper = Model.BASE

    stt = WhisperSTTService(
        model=whisper,
        device=whisper_device,
        compute_type=whisper_compute,
    )
    interview = BrandInterviewProcessor(
        backend=backend,
        read_questions_aloud=cfg["read_questions_aloud"],
    )

    pipeline = Pipeline(
        [
            transport.input(),
            vad,
            stt,
            interview,
            transport.output(),
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=False,
            enable_usage_metrics=False,
        ),
    )
    runner = WorkerRunner()
    await runner.add_workers(worker)
    await runner.run()


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
