from fastapi import APIRouter, HTTPException

from repositories.brand_profile_repository import (
    BrandProfileRepository
)
from repositories.voice_sample_repository import (
    VoiceSampleRepository
)
from repositories.interview_answer_repository import (
    InterviewAnswerRepository
)
from repositories.interview_session_repository import (
    InterviewSessionRepository
)
from services.interview_session_sync import (
    backfill_interview_answers_from_sessions,
)
from services.corpus_service import CorpusService

from models.brand_profile_request import (
    BrandProfileRequest
)
from models.voice_sample import (
    VoiceSampleRequest
)
from models.interview_answer import (
    InterviewAnswersSaveRequest
)

from utils.promise_completeness import (
    promise_warnings
)
from services.brand_setup_status import (
    enrich_profile_with_setup,
)


router = APIRouter(
    prefix="/brand-profiles",
    tags=["Brand Profiles"]
)


brand_repository = BrandProfileRepository()

voice_sample_repository = VoiceSampleRepository()

interview_answer_repository = (
    InterviewAnswerRepository()
)

interview_session_repository = InterviewSessionRepository()

corpus_service = CorpusService()


VOICE_SAMPLE_SOURCES = {"paste", "audio", "studio_edit"}

INTERVIEW_ANSWER_SOURCES = {"type", "audio"}


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

    result = (
        brand_repository
        .get_profile(profile_id, user_id)
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return result


def _reject_empty(value: str, field_name: str):

    if not (value or "").strip():
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} is empty"
        )


def _reject_unknown_source(
    source: str,
    allowed: set[str]
):

    if source not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Unknown source"
        )


def _with_promise_warnings(profile: dict) -> dict:

    return {
        **profile,
        "promise_warnings": promise_warnings(profile)
    }


# -----------------------------------
# CREATE BRAND PROFILE
# -----------------------------------

@router.post("/")
async def create_brand_profile(
    profile: BrandProfileRequest
):

    profile_data = profile.model_dump()

    result = (
        brand_repository
        .create_profile(profile_data)
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to create brand profile"
        )

    return {
        "success": True,
        "brand_profile": result[0]
    }

# -----------------------------------
# GET USER BRAND PROFILES
# -----------------------------------

@router.get("/user/{user_id}")
async def get_user_brand_profiles(
    user_id: str
):

    result = (
        brand_repository
        .get_user_profiles(user_id)
    )

    material_by_profile = corpus_service.repository.list_counts_by_user(
        user_id,
    )

    enriched_profiles = []
    for profile in result:
        profile_id = str(profile.get("id"))
        count = material_by_profile.get(profile_id, 0)
        if count == 0:
            corpus_service.backfill_from_legacy_if_empty(
                profile_id,
                user_id,
            )
            count = corpus_service.material_count(profile_id, user_id)
        enriched_profiles.append(
            enrich_profile_with_setup(
                _with_promise_warnings(profile),
                count,
            )
        )

    return {
        "success": True,
        "brand_profiles": enriched_profiles,
    }


# -----------------------------------
# GET BRAND PROFILE
# -----------------------------------

@router.get("/{profile_id}")
async def get_brand_profile(
    profile_id: str
):

    result = (
        brand_repository
        .get_profile(profile_id)
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    profile = result[0]
    warnings = promise_warnings(profile)

    return {
        "success": True,
        "brand_profile": profile,
        "promise_warnings": warnings
    }




# -----------------------------------
# UPDATE BRAND PROFILE
# -----------------------------------

@router.put("/{profile_id}")
async def update_brand_profile(
    profile_id: str,
    profile: BrandProfileRequest
):

    payload = profile.model_dump()
    target = str(payload.get("target_audience") or "").strip()
    not_for = str(payload.get("not_for") or "").strip()

    if target or not_for:
        field_errors: dict[str, str] = {}
        if not target:
            field_errors["target_audience"] = "Who you help is required."
        if not not_for:
            field_errors["not_for"] = "Who you are not for is required."
        if field_errors:
            raise HTTPException(
                status_code=422,
                detail={
                    "success": False,
                    "fields": field_errors,
                },
            )

    result = (
        brand_repository
        .update_profile(
            profile_id,
            payload
        )
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return {
        "success": True,
        "brand_profile": result[0]
    }


# -----------------------------------
# DELETE BRAND PROFILE
# -----------------------------------

@router.delete("/{profile_id}")
async def delete_brand_profile(
    profile_id: str
):

    result = (
        brand_repository
        .delete_profile(profile_id)
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return {
        "success": True,
        "message": "Brand profile deleted"
    }


# -----------------------------------
# ADD VOICE SAMPLE
# -----------------------------------

@router.post("/{profile_id}/samples")
async def add_voice_sample(
    profile_id: str,
    sample: VoiceSampleRequest,
    user_id: str | None = None
):

    owner_id = _require_user_id(
        user_id,
        sample.user_id
    )

    _require_owned_profile(profile_id, owner_id)

    _reject_unknown_source(
        sample.source,
        VOICE_SAMPLE_SOURCES
    )

    _reject_empty(sample.content, "content")

    if sample.source == "paste":
        corpus_source = "paste"
    elif sample.source == "studio_edit":
        corpus_source = "studio_edit"
    else:
        corpus_source = "legacy_transcript"

    corpus_row = corpus_service.append_paste(
        owner_id=owner_id,
        profile_id=profile_id,
        content=sample.content,
        source=corpus_source,
    )

    if not corpus_row:
        raise HTTPException(
            status_code=500,
            detail="Failed to save voice sample"
        )

    return {
        "success": True,
        "voice_sample": {
            "id": corpus_row.get("id"),
            "user_id": owner_id,
            "brand_profile_id": profile_id,
            "source": sample.source,
            "content": corpus_row.get("content"),
            "created_at": corpus_row.get("created_at"),
        },
        "corpus_item": corpus_row,
    }


# -----------------------------------
# LIST VOICE SAMPLES
# -----------------------------------

@router.get("/{profile_id}/samples")
async def list_voice_samples(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    corpus_service.backfill_from_legacy_if_empty(profile_id, user_id)
    items = corpus_service.list_items(profile_id, user_id)

    legacy_samples = [
        {
            "id": item.get("id"),
            "user_id": item.get("user_id"),
            "brand_profile_id": item.get("brand_profile_id"),
            "source": (
                "paste"
                if item.get("source") in {"paste", "type", "studio_edit"}
                else "audio"
            ),
            "content": item.get("content"),
            "created_at": item.get("created_at"),
        }
        for item in items
    ]

    return {
        "success": True,
        "voice_samples": legacy_samples,
    }


# -----------------------------------
# SAVE INTERVIEW ANSWERS
# -----------------------------------

@router.put("/{profile_id}/interview-answers")
async def save_interview_answers(
    profile_id: str,
    payload: InterviewAnswersSaveRequest,
    user_id: str | None = None
):

    owner_id = _require_user_id(
        user_id,
        payload.user_id
    )

    _require_owned_profile(profile_id, owner_id)

    rows = []

    for answer in payload.answers:

        _reject_unknown_source(
            answer.source,
            INTERVIEW_ANSWER_SOURCES
        )

        _reject_empty(
            answer.question_key,
            "question_key"
        )

        _reject_empty(
            answer.answer_text,
            "content"
        )

        rows.append({
            "user_id": owner_id,
            "brand_profile_id": profile_id,
            "question_key": answer.question_key,
            "question_text": answer.question_text,
            "answer_text": answer.answer_text,
            "source": answer.source
        })

    inserted = []
    for row in rows:
        item = corpus_service.append_paste(
            owner_id=owner_id,
            profile_id=profile_id,
            content=row["answer_text"],
            source="type",
            theme=row["question_key"],
            question_text=row["question_text"],
        )
        if item:
            inserted.append({
                "id": item.get("id"),
                "user_id": owner_id,
                "brand_profile_id": profile_id,
                "question_key": row["question_key"],
                "question_text": row["question_text"],
                "answer_text": row["answer_text"],
                "source": row["source"],
                "created_at": item.get("created_at"),
                "updated_at": item.get("created_at"),
            })

    return {
        "success": True,
        "interview_answers": inserted,
    }


# -----------------------------------
# LIST INTERVIEW ANSWERS
# -----------------------------------

@router.get("/{profile_id}/interview-answers")
async def list_interview_answers(
    profile_id: str,
    user_id: str
):

    _require_owned_profile(profile_id, user_id)

    corpus_service.backfill_from_legacy_if_empty(profile_id, user_id)
    items = corpus_service.list_items(profile_id, user_id)

    legacy_answers = [
        {
            "id": item.get("id"),
            "user_id": item.get("user_id"),
            "brand_profile_id": item.get("brand_profile_id"),
            "question_key": item.get("theme") or "",
            "question_text": item.get("question_text") or "",
            "answer_text": item.get("content"),
            "source": (
                "audio"
                if item.get("source") in {"full_talk", "mini_talk", "legacy_transcript"}
                else "type"
            ),
            "created_at": item.get("created_at"),
            "updated_at": item.get("created_at"),
        }
        for item in items
        if item.get("theme")
    ]

    if not legacy_answers:
        sessions = interview_session_repository.list_recent_sessions(
            profile_id,
            user_id,
        )
        backfill_interview_answers_from_sessions(
            brand_profile_id=profile_id,
            user_id=user_id,
            sessions=sessions,
        )
        items = corpus_service.list_items(profile_id, user_id)
        legacy_answers = [
            {
                "id": item.get("id"),
                "user_id": item.get("user_id"),
                "brand_profile_id": item.get("brand_profile_id"),
                "question_key": item.get("theme") or "",
                "question_text": item.get("question_text") or "",
                "answer_text": item.get("content"),
                "source": "type",
                "created_at": item.get("created_at"),
                "updated_at": item.get("created_at"),
            }
            for item in items
            if item.get("theme")
        ]

    return {
        "success": True,
        "interview_answers": legacy_answers,
    }


# -----------------------------------
# LIST CORPUS ITEMS (source of truth)
# -----------------------------------

@router.get("/{profile_id}/corpus-items")
async def list_corpus_items(
    profile_id: str,
    user_id: str,
):

    _require_owned_profile(profile_id, user_id)

    corpus_service.backfill_from_legacy_if_empty(profile_id, user_id)
    items = corpus_service.list_items(profile_id, user_id)

    return {
        "success": True,
        "corpus_items": items,
        "material_count": len(items),
    }
