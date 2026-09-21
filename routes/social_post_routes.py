from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from repositories.social_post_repository import (
    SocialPostRepository
)
from services.post_actions import allowed_actions
from services.supabase_storage_service import (
    SupabaseStorageService
)
from workflows.social_content_workflow import SocialContentWorkflow
from repositories.brand_profile_repository import BrandProfileRepository
from models.brand_profile import BrandProfile
from services.brand_dna_service import BrandDnaService
router = APIRouter(
    prefix="/api/social-posts",
    tags=["Social Posts"]
)


social_post_repository = SocialPostRepository()

supabase_storage = SupabaseStorageService()

social_content_workflow = SocialContentWorkflow()

brand_repository = BrandProfileRepository()

brand_dna_service = BrandDnaService()

class SchedulePostRequest(BaseModel):

    scheduled_at: datetime

    timezone: str = "Asia/Kolkata"

class UpdateSocialPostRequest(BaseModel):
    headline: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    call_to_action: str | None = None
    image_prompt: str | None = None
# -----------------------------------
# GET USER POSTS
# -----------------------------------

@router.get("/user/{user_id}")
async def get_user_posts(
    user_id: str,
    status: str | None = None
):

    try:

        posts = (
            social_post_repository
            .get_user_posts(
                user_id=user_id,
                status=status
            )
        )

        enriched = []

        for post in posts:
            row = dict(post)
            image_path = row.get("image_url")
            if image_path:
                row["image_signed_url"] = (
                    supabase_storage
                    .create_image_signed_url(
                        storage_path=image_path,
                        expires_in=3600
                    )
                )
            enriched.append(row)

        return {
            "success": True,
            "count": len(enriched),
            "data": enriched
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# -----------------------------------
# GET SINGLE POST
# -----------------------------------

@router.get("/{post_id}")
async def get_post(post_id: str):

    try:

        posts = social_post_repository.get_post(
            post_id
        )

        if not posts:
            raise HTTPException(
                status_code=404,
                detail="Social post not found"
            )

        post = posts[0]

        # -----------------------------------
        # CREATE TEMPORARY IMAGE URL
        # -----------------------------------

        image_path = post.get("image_url")

        image_signed_url = None

        if image_path:
            image_signed_url = (
                supabase_storage
                .create_image_signed_url(
                    storage_path=image_path,
                    expires_in=3600
                )
            )

        review = post.get("review")

        return {
            "success": True,
            "post": post,
            "image_signed_url": image_signed_url,
            "review": review,
            "allowed_actions": allowed_actions(post.get("status")),
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@router.post("/{post_id}/approve")
async def approve_post(post_id: str):
    try:
        posts = social_post_repository.get_post(post_id)

        if not posts:
            raise HTTPException(
                status_code=404,
                detail="Social post not found"
            )

        post = posts[0]

        current_status = post.get("status")

        # Prevent approving a post that is already processed
        if current_status in ["scheduled", "publishing", "published"]:
            raise HTTPException(
                status_code=400,
                detail=f"Post cannot be approved from status '{current_status}'"
            )

        result = social_post_repository.update_post(
            post_id=post_id,
            post_data={
                "status": "approved"
            }
        )

        return {
            "success": True,
            "message": "Social post approved successfully",
            "post": result[0] if result else None
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
    
@router.put("/{post_id}")
async def update_post(
    post_id: str,
    request: UpdateSocialPostRequest
):
    try:
        posts = social_post_repository.get_post(post_id)

        if not posts:
            raise HTTPException(
                status_code=404,
                detail="Social post not found"
            )

        update_data = request.model_dump(
            exclude_unset=True
        )

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        result = social_post_repository.update_post(
            post_id=post_id,
            post_data=update_data
        )

        return {
            "success": True,
            "message": "Social post updated successfully",
            "post": result[0] if result else None
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
# -----------------------------------
# SCHEDULE POST
# -----------------------------------

@router.put("/{post_id}/schedule")
async def schedule_post(
    post_id: str,
    request: SchedulePostRequest
):

    try:

        # Check post exists
        posts = (
            social_post_repository
            .get_post(post_id)
        )

        if not posts:

            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

        # Schedule
        result = (
            social_post_repository
            .schedule_post(
                post_id=post_id,
                scheduled_at=request.scheduled_at.isoformat(),
                timezone=request.timezone
            )
        )

        return {
            "success": True,
            "message": "Post scheduled successfully",
            "data": result[0] if result else None
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

@router.post("/{post_id}/regenerate")
async def regenerate_post(post_id: str):
    try:
        posts = social_post_repository.get_post(post_id)

        if not posts:
            raise HTTPException(
                status_code=404,
                detail="Social post not found"
            )

        post = posts[0]

        user_id = post.get("user_id")
        brand_profile_id = post.get("brand_profile_id")

        if not brand_profile_id:
            raise HTTPException(
                status_code=400,
                detail="Post is not associated with a brand profile"
            )

        brand_data = brand_repository.get_profile(
            profile_id=brand_profile_id,
            user_id=user_id
        )

        if not brand_data:
            raise HTTPException(
                status_code=404,
                detail="Brand profile not found for this user"
            )

        profile_row = brand_data[0]
        brand_profile = BrandProfile(
            **profile_row
        )

        platform = (post.get("platform") or "instagram").strip().lower()
        regen_topic = (
            post.get("topic")
            or post.get("caption")
            or ""
        )
        dna_context = brand_dna_service.build_generation_context(
            profile_row,
            brand_profile_id,
            user_id,
            platform,
            topic=str(regen_topic),
        )

        result = await social_content_workflow.regenerate(
            post_id=post_id,
            brand_profile=brand_profile,
            brand_dna_context=dna_context,
        )

        return result

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )