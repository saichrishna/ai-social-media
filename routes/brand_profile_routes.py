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


router = APIRouter(
    prefix="/brand-profiles",
    tags=["Brand Profiles"]
)


brand_repository = BrandProfileRepository()

voice_sample_repository = VoiceSampleRepository()

interview_answer_repository = (
    InterviewAnswerRepository()
)


VOICE_SAMPLE_SOURCES = {"paste", "audio"}

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

    return {
        "success": True,
        "brand_profiles": [
            _with_promise_warnings(profile)
            for profile in result
        ]
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

    result = (
        brand_repository
        .update_profile(
            profile_id,
            profile.model_dump()
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

    result = (
        voice_sample_repository
        .create_sample({
            "user_id": owner_id,
            "brand_profile_id": profile_id,
            "source": sample.source,
            "content": sample.content
        })
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to save voice sample"
        )

    return {
        "success": True,
        "voice_sample": result[0]
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

    result = (
        voice_sample_repository
        .get_samples(
            brand_profile_id=profile_id,
            user_id=user_id
        )
    )

    return {
        "success": True,
        "voice_samples": result
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

    result = (
        interview_answer_repository
        .upsert_answers(rows)
    )

    return {
        "success": True,
        "interview_answers": result
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

    result = (
        interview_answer_repository
        .get_answers(
            brand_profile_id=profile_id,
            user_id=user_id
        )
    )

    return {
        "success": True,
        "interview_answers": result
    }
