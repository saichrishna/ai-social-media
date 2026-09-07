from fastapi import APIRouter, HTTPException

from repositories.social_post_repository import (
    SocialPostRepository
)
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/social-posts",
    tags=["Social Posts"]
)


social_post_repository = SocialPostRepository()

class SchedulePostRequest(BaseModel):

    scheduled_at: datetime

    timezone: str = "Asia/Kolkata"

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

        return {
            "success": True,
            "count": len(posts),
            "data": posts
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

        posts = (
            social_post_repository
            .get_post(post_id)
        )

        if not posts:

            raise HTTPException(
                status_code=404,
                detail="Post not found"
            )

        return {
            "success": True,
            "data": posts[0]
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