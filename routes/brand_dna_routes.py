from fastapi import APIRouter, HTTPException, UploadFile, File

from repositories.brand_profile_repository import (
    BrandProfileRepository
)
from repositories.interview_session_repository import (
    InterviewSessionRepository
)
from repositories.interview_answer_repository import (
    InterviewAnswerRepository
)
from repositories.voice_sample_repository import (
    VoiceSampleRepository
)
from repositories.voice_study_repository import (
    VoiceStudyRepository
)
from repositories.channel_preference_repository import (
    ChannelPreferenceRepository
)

from models.brand_dna_models import (
    StartInterviewSessionRequest,
    InterviewAnswerStepRequest,
    CompleteInterviewSessionRequest,
    ChannelPreferenceRequest,
    DraftGenerateRequest,
)
from models.brand_profile import BrandProfile

from services.interview_prep_service import InterviewPrepService
from services.interview_session_sync import (
    build_interview_transcript,
    sync_session_to_your_words,
)
from services.speech_to_text_service import SpeechToTextService
from services.voice_study_service import VoiceStudyService
from services.brand_dna_service import BrandDnaService
from workflows.social_content_workflow import SocialContentWorkflow


router = APIRouter(
    prefix="/brand-profiles",
    tags=["Brand DNA"]
)


brand_repository = BrandProfileRepository()
session_repository = InterviewSessionRepository()
answer_repository = InterviewAnswerRepository()
sample_repository = VoiceSampleRepository()
study_repository = VoiceStudyRepository()
channel_repository = ChannelPreferenceRepository()

prep_service = InterviewPrepService()
stt_service = SpeechToTextService()
voice_study_service = VoiceStudyService()
brand_dna_service = BrandDnaService()
social_content_workflow = SocialContentWorkflow()


def _require_user_id(
    query_user_id: str | None,
    body_user_id: str | None = None
) -> str:

    owner_id = query_user_id or body_user_id or ""

    if not owner_id.strip():
        raise HTTPException(
            status_code=400,
            detail="user_id is required"
        )

    if (
        query_user_id
        and body_user_id
        and query_user_id != body_user_id
    ):
        raise HTTPException(
            status_code=400,
            detail="user_id mismatch"
        )

    return owner_id


def _require_owned_profile(
    profile_id: str,
    user_id: str
):

    result = brand_repository.get_profile(
        profile_id,
        user_id
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return result[0]


def _next_unanswered_question(questions: list) -> dict | None:

    for question in questions:
        if not question.get("answered"):
            return question

    return None


# -----------------------------------
# INTERVIEW SESSIONS
# -----------------------------------

@router.post("/{profile_id}/interview-sessions")
async def start_interview_session(
    profile_id: str,
    payload: StartInterviewSessionRequest,
    user_id: str | None = None,
    force_new: bool = False,
):

    owner_id = _require_user_id(
        user_id,
        payload.user_id
    )

    profile = _require_owned_profile(
        profile_id,
        owner_id
    )

    active = session_repository.get_active_session(
        profile_id,
        owner_id
    )

    if active and force_new:
        from datetime import datetime, timezone

        closing = active[0]
        sync_session_to_your_words(
            closing,
            owner_id=owner_id,
            profile_id=profile_id,
            session_id=closing.get("id"),
            capture_mode=closing.get("capture_mode"),
        )
        session_repository.update_session(
            closing["id"],
            {
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        active = None

    if active:
        return {
            "success": True,
            "interview_session": active[0],
            "resumed": True,
        }

    mode = (payload.mode or "full").strip().lower()
    if mode not in {"full", "mini"}:
        raise HTTPException(
            status_code=400,
            detail="mode must be full or mini",
        )

    cold_open = payload.cold_open_answer.strip()

    if mode == "mini":
        from services.interview_plans import build_mini_session_plan

        plan = build_mini_session_plan(
            profile,
            cold_open,
        )
    else:
        plan = await prep_service.build_session_plan(
            profile,
            cold_open,
        )

    result = session_repository.create_session({
        "user_id": owner_id,
        "brand_profile_id": profile_id,
        "status": "in_progress",
        "prep_brief": plan["prep_brief"],
        "questions": plan["questions"],
        "transcript": cold_open or f"[{mode} capture]",
        "follow_up_used": False,
    })

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to start interview session"
        )

    return {
        "success": True,
        "interview_session": result[0],
        "resumed": False,
        "stt_available": stt_service.is_available()
    }


@router.get("/{profile_id}/interview-sessions/active")
async def get_active_interview_session(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    active = session_repository.get_active_session(
        profile_id,
        user_id
    )

    return {
        "success": True,
        "interview_session": active[0] if active else None,
        "stt_available": stt_service.is_available()
    }


@router.get(
    "/{profile_id}/interview-sessions/{session_id}"
)
async def get_interview_session(
    profile_id: str,
    session_id: str,
    user_id: str,
):

    if session_id == "active":
        raise HTTPException(
            status_code=404,
            detail="Interview session not found",
        )

    _require_owned_profile(profile_id, user_id)

    rows = session_repository.get_session(
        session_id,
        profile_id,
        user_id,
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found",
        )

    return {
        "success": True,
        "interview_session": rows[0],
        "stt_available": stt_service.is_available(),
    }


@router.post(
    "/{profile_id}/interview-sessions/{session_id}/answer"
)
async def save_interview_step_answer(
    profile_id: str,
    session_id: str,
    payload: InterviewAnswerStepRequest,
    user_id: str | None = None
):

    owner_id = _require_user_id(
        user_id,
        payload.user_id
    )

    _require_owned_profile(profile_id, owner_id)

    rows = session_repository.get_session(
        session_id,
        profile_id,
        owner_id
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    session = rows[0]

    if session.get("status") != "in_progress":
        raise HTTPException(
            status_code=400,
            detail="Interview session is not active"
        )

    answer_text = payload.answer_text.strip()

    if not answer_text:
        raise HTTPException(
            status_code=400,
            detail="content is empty"
        )

    if payload.source not in {"type", "audio"}:
        raise HTTPException(
            status_code=400,
            detail="Unknown source"
        )

    questions = session.get("questions") or []

    updated_questions = []

    matched = False

    for question in questions:
        if question.get("question_key") == payload.question_key:
            matched = True
            updated_questions.append({
                **question,
                "answer_text": answer_text,
                "source": payload.source,
                "answered": True
            })
        else:
            updated_questions.append(question)

    if not matched:
        raise HTTPException(
            status_code=400,
            detail="Unknown question_key"
        )

    patch = session_repository.update_session(
        session_id,
        {
            "questions": updated_questions,
        }
    )

    return {
        "success": True,
        "interview_session": patch[0] if patch else None,
        "next_question": _next_unanswered_question(
            updated_questions
        )
    }


@router.post(
    "/{profile_id}/interview-sessions/{session_id}/transcribe"
)
async def transcribe_interview_audio(
    profile_id: str,
    session_id: str,
    user_id: str,
    file: UploadFile = File(...)
):

    _require_owned_profile(profile_id, user_id)

    rows = session_repository.get_session(
        session_id,
        profile_id,
        user_id
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    audio_bytes = await file.read()

    if not audio_bytes:
        raise HTTPException(
            status_code=400,
            detail="Empty audio upload"
        )

    try:
        text = stt_service.transcribe_bytes(
            audio_bytes,
            filename=file.filename or "audio.webm"
        )
    except RuntimeError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error)
        ) from error
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    return {
        "success": True,
        "transcript_text": text
    }


@router.post(
    "/{profile_id}/interview-sessions/{session_id}/complete"
)
async def complete_interview_session(
    profile_id: str,
    session_id: str,
    payload: CompleteInterviewSessionRequest,
    user_id: str | None = None
):

    owner_id = _require_user_id(
        user_id,
        payload.user_id
    )

    _require_owned_profile(profile_id, owner_id)

    rows = session_repository.get_session(
        session_id,
        profile_id,
        owner_id
    )

    if not rows:
        raise HTTPException(
            status_code=404,
            detail="Interview session not found"
        )

    session = rows[0]
    questions = session.get("questions") or []

    transcript = (
        payload.transcript.strip()
        or build_interview_transcript({**session, "questions": questions})
        or session.get("transcript")
        or ""
    ).strip()

    sync_session_to_your_words(
        {**session, "questions": questions},
        owner_id=owner_id,
        profile_id=profile_id,
        session_id=session_id,
        capture_mode=session.get("capture_mode"),
    )

    from datetime import datetime, timezone

    completed = session_repository.update_session(
        session_id,
        {
            "status": "completed",
            "transcript": transcript,
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat()
        }
    )

    return {
        "success": True,
        "interview_session": completed[0] if completed else None
    }


# -----------------------------------
# VOICE STUDY (STAGE 3)
# -----------------------------------

@router.post("/{profile_id}/voice-study")
async def run_voice_study(
    profile_id: str,
    user_id: str
):

    profile = _require_owned_profile(
        profile_id,
        user_id
    )

    try:
        study = await voice_study_service.run_study(
            profile_id,
            user_id,
            profile
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        ) from error

    saved = study_repository.create_study({
        "user_id": user_id,
        "brand_profile_id": profile_id,
        "keep_items": study["keep_items"],
        "raise_items": study["raise_items"],
        "source_summary": study["source_summary"]
    })

    return {
        "success": True,
        "voice_study": saved[0] if saved else study
    }


@router.get("/{profile_id}/voice-study/latest")
async def get_latest_voice_study(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    rows = study_repository.get_latest_study(
        profile_id,
        user_id
    )

    return {
        "success": True,
        "voice_study": rows[0] if rows else None,
        "corpus_count": brand_dna_service.corpus_item_count(
            profile_id,
            user_id
        )
    }


# -----------------------------------
# CHANNEL PREFERENCES
# -----------------------------------

@router.put("/{profile_id}/channel-preferences")
async def upsert_channel_preference(
    profile_id: str,
    payload: ChannelPreferenceRequest,
    user_id: str | None = None
):

    owner_id = _require_user_id(
        user_id,
        payload.user_id
    )

    _require_owned_profile(profile_id, owner_id)

    platform = payload.platform.strip().lower()

    if platform not in {"instagram", "linkedin", "facebook"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported platform"
        )

    result = channel_repository.upsert_preference({
        "user_id": owner_id,
        "brand_profile_id": profile_id,
        "platform": platform,
        "tone_notes": payload.tone_notes.strip(),
        "length_notes": payload.length_notes.strip(),
        "hashtag_notes": payload.hashtag_notes.strip()
    })

    return {
        "success": True,
        "channel_preference": result[0] if result else None
    }


@router.get("/{profile_id}/channel-preferences")
async def list_channel_preferences(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    rows = channel_repository.list_preferences(
        profile_id,
        user_id
    )

    return {
        "success": True,
        "channel_preferences": rows
    }


# -----------------------------------
# DRAFT (STAGE 4)
# -----------------------------------

@router.get("/{profile_id}/draft-topics")
async def list_draft_topics(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    topics = brand_dna_service.suggest_draft_topics(
        profile_id,
        user_id
    )

    return {
        "success": True,
        "topics": topics,
        "ready": brand_dna_service.has_minimum_corpus(
            profile_id,
            user_id
        )
    }


@router.post("/{profile_id}/draft-generate")
async def generate_brand_draft(
    profile_id: str,
    payload: DraftGenerateRequest
):

    profile_row = _require_owned_profile(
        profile_id,
        payload.user_id
    )

    if not brand_dna_service.has_minimum_corpus(
        profile_id,
        payload.user_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Give us something only you know first — "
                "at least three pastes or answers."
            )
        )

    topic = payload.topic.strip()

    if not topic:
        raise HTTPException(
            status_code=400,
            detail="topic is required"
        )

    platform = payload.platform.strip().lower() or "instagram"

    brand_profile = BrandProfile(**profile_row)

    dna_context = brand_dna_service.build_generation_context(
        profile_row,
        profile_id,
        payload.user_id,
        platform,
        topic=topic,
    )

    try:
        result = await social_content_workflow.generate(
            topic=topic,
            description=payload.description.strip(),
            platform=platform,
            brand_profile=brand_profile,
            user_id=payload.user_id,
            brand_profile_id=profile_id,
            social_account_id=None,
            brand_dna_context=dna_context
        )
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        ) from error

    return result
