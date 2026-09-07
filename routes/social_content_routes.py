from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from repositories.brand_profile_repository import BrandProfileRepository
from workflows.social_content_workflow import SocialContentWorkflow
from models.brand_profile import BrandProfile


router = APIRouter(
    prefix="/api/social-content",
    tags=["Social Content"]
)


class GenerateSocialContentRequest(BaseModel):

    user_id: str

    brand_profile_id: str

    topic: str

    description: str = ""

    platform: str = "instagram"

    max_attempts: int = 3


brand_profile_repository = BrandProfileRepository()

social_content_workflow = SocialContentWorkflow()


@router.post("/generate")
async def generate_social_content(
    request: GenerateSocialContentRequest
):

    try:

        # -----------------------------------
        # FETCH BRAND PROFILE
        # -----------------------------------

        profiles = (
            brand_profile_repository
            .get_profile(
                request.brand_profile_id,
                request.user_id
            )
        )

        if not profiles:
            raise HTTPException(
                status_code=404,
                detail="Brand profile not found"
            )

        profile_data = profiles[0]


        # -----------------------------------
        # CONVERT TO PYDANTIC MODEL
        # -----------------------------------

        brand_profile = BrandProfile(
            business_name=profile_data["business_name"],
            industry=profile_data["industry"],
            location=profile_data["location"],
            services=profile_data["services"],
            brand_voice=profile_data["brand_voice"],
            target_audience=profile_data["target_audience"],
            preferred_hashtags=profile_data["preferred_hashtags"],
            forbidden_topics=profile_data["forbidden_topics"],
            additional_instructions=profile_data[
                "additional_instructions"
            ]
        )

        # -----------------------------------
        # RUN AI WORKFLOW
        # -----------------------------------

        result = await social_content_workflow.generate(

            topic=request.topic,

            description=request.description,

            platform=request.platform,

            brand_profile=brand_profile,

            user_id=request.user_id,

            brand_profile_id=request.brand_profile_id,

            max_attempts=request.max_attempts
        )

        return result

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )