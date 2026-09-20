from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from services.ollama_service import OllamaService
from pathlib import Path
import uuid
from agents.content_strategist import ContentStrategist
from agents.prompt_engineer import PromptEngineer
from agents.content_generator import ContentGenerator
from agents.content_reviewer import ContentReviewer
from workflows.social_content_workflow import SocialContentWorkflow
from models.brand_profile import BrandProfile
from routes.brand_profile_routes import router as brand_profile_router
from routes.brand_dna_routes import router as brand_dna_router
from services.supabase_storage_service import (
    SupabaseStorageService
)
from models.brand_profile import BrandProfile
from repositories.brand_profile_repository import BrandProfileRepository
from routes.user_routes import router as user_router
from routes.social_post_routes import (
    router as social_post_router
)
from routes.social_content_routes import (
    router as social_content_router
)
from routes.social_account_routes import (
    router as social_account_router
)
from routes.social_connect_routes import (
    router as social_connect_router
)
from image_generation.comfyui_service import ComfyUIService

from contextlib import asynccontextmanager
import asyncio

from services.scheduler_service import SchedulerService
from services.brand_dna_service import BrandDnaService
from services.brand_setup_status import (
    derive_setup_status,
    user_safe_not_ready_message,
)

scheduler_service = SchedulerService()
comfyui_service = ComfyUIService()

@asynccontextmanager
async def lifespan(app: FastAPI):

    scheduler_task = asyncio.create_task(
        scheduler_service.start()
    )

    yield

    scheduler_service.is_running = False

    scheduler_task.cancel()
    
app = FastAPI(
title="AI Social Media Backend",
version="1.0.0",
lifespan=lifespan

)

app.include_router(
    brand_profile_router
)

app.include_router(
    brand_dna_router
)

app.include_router(user_router)


app.include_router(
    social_content_router
)

app.include_router(
    social_post_router
)

app.include_router(
    social_account_router
)
app.include_router(
    social_connect_router
)

# -----------------------------------

# SERVICES / AGENTS

# -----------------------------------

ollama_service = OllamaService()

content_strategist = ContentStrategist()

prompt_engineer = PromptEngineer()

content_generator = ContentGenerator()

content_reviewer = ContentReviewer()

social_content_workflow = SocialContentWorkflow()

supabase_storage = SupabaseStorageService()

brand_repository = BrandProfileRepository()

brand_dna_service = BrandDnaService()

# -----------------------------------

# REQUEST MODELS

# -----------------------------------

class ImageGenerationRequest(BaseModel):
    post_id: str

class ChatRequest(BaseModel):
    question: str

class ContentStrategistRequest(BaseModel):
    question: str = ""
    platform: str = "instagram"
    number_of_topics: int = 5
    business_goal: str = ""
    brand_profile: BrandProfile | None = None

class PromptEngineerRequest(BaseModel):
    topic: str
    description: str = ""

class ContentGeneratorRequest(BaseModel):
    prompt: str
    platform: str = "instagram"

class ContentReviewerRequest(BaseModel):
    headline: str
    caption: str
    hashtags: list[str]
    call_to_action: str
    platform: str = "instagram"

class SocialContentRequest(BaseModel):
    user_id: str
    brand_profile_id: str
    topic: str
    description: str = ""
    platform: str = "instagram"

# -----------------------------------

# HELPER: BUILD BRAND CONTEXT

# -----------------------------------

def build_brand_context(brand_profile: BrandProfile | None) -> str:
    if not brand_profile:
        return ""

    return f"""
    ```

    BUSINESS NAME:
    {brand_profile.business_name}

    INDUSTRY:
    {brand_profile.industry}

    LOCATION:
    {brand_profile.location}

    BRAND VOICE:
    {brand_profile.brand_voice}

    TARGET AUDIENCE:
    {brand_profile.target_audience}

    SERVICES:
    {", ".join(brand_profile.services)}

    PREFERRED HASHTAGS:
    {", ".join(brand_profile.preferred_hashtags)}

    FORBIDDEN TOPICS:
    {", ".join(brand_profile.forbidden_topics)}

    ADDITIONAL INSTRUCTIONS:
    {brand_profile.additional_instructions}
    """

    # -----------------------------------

    # HOME

# -----------------------------------

@app.get("/")
async def home():

    return {
    "message": "AI Social Media Backend is running"
    }


# -----------------------------------

# TEST OLLAMA

# -----------------------------------

@app.post("/test-ollama")
async def test_ollama(request: ChatRequest):

    try:

        response = await ollama_service.chat(
            system_prompt=(
                "You are an AI assistant helping build "
                "an automated social media platform."
            ),
            user_prompt=request.question
        )

        return {
            "success": True,
            "response": response
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

# -----------------------------------

# CONTENT STRATEGIST

# -----------------------------------

@app.post("/api/content-strategist")
async def generate_content_topics(request: ContentStrategistRequest):

    try:

        # Build brand-aware context
        brand_context = build_brand_context(
            request.brand_profile
        )

        # Generate strategy + topics
        result = await content_strategist.generate_topics(

            question=request.question,

            platform=request.platform,

            brand_context=brand_context,

            number_of_topics=request.number_of_topics,

            business_goal=request.business_goal
        )

        return {
            "success": True,

            "brand": (
                request.brand_profile.model_dump()
                if request.brand_profile
                else None
            ),

            "data": result
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

# -----------------------------------

# PROMPT ENGINEER

# -----------------------------------

@app.post("/api/prompt-engineer")
async def generate_prompt(request: PromptEngineerRequest):


    try:
        result = await prompt_engineer.generate_prompt(
            topic=request.topic,
            description=request.description
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

# -----------------------------------

# CONTENT GENERATOR

# -----------------------------------

@app.post("/api/content-generator")
async def generate_content(request: ContentGeneratorRequest):

    try:

        result = await content_generator.generate_content(
            prompt=request.prompt,
            platform=request.platform
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

# -----------------------------------

# CONTENT REVIEWER

# -----------------------------------

@app.post("/api/content-reviewer")
async def review_content(request: ContentReviewerRequest):


    try:
        result = await content_reviewer.review_content(

            headline=request.headline,

            caption=request.caption,

            hashtags=request.hashtags,

            call_to_action=request.call_to_action,

            platform=request.platform
        )

        return {
            "success": True,
            "data": result
        }

    except Exception as error:

        raise HTTPException(
        status_code=500,
        detail=str(error)
    )

@app.post("/api/generate-image")
async def generate_image(request: ImageGenerationRequest):

    try:

        # 1. Get the social post
        post = supabase_storage.get_social_post(
            request.post_id
        )

        # 2. Make sure the post has an image prompt
        image_prompt = post.get("image_prompt")

        if not image_prompt:
            raise ValueError(
                "This social post does not have an image_prompt."
            )

        # 3. Generate image using ComfyUI
        image_path = comfyui_service.generate_image(
            prompt=image_prompt
        )

        # 4. Create a unique Storage path
        filename = Path(image_path).name

        storage_path = (
            f"generated/"
            f"{request.post_id}/"
            f"{uuid.uuid4()}_{filename}"
        )

        # 5. Upload to Supabase Storage
        uploaded_path = (
            supabase_storage.upload_image(
                local_path=image_path,
                storage_path=storage_path
            )
        )

        # 6. Link image to the social post
        updated_post = (
            supabase_storage.update_post_image(
                post_id=request.post_id,
                image_path=uploaded_path
            )
        )

        return {
            "success": True,
            "post_id": request.post_id,
            "image_path": uploaded_path,
            "post": updated_post
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
# -----------------------------------

# FULL SOCIAL CONTENT WORKFLOW

# -----------------------------------

@app.post("/api/generate-social-content")
async def generate_social_content(
    request: SocialContentRequest
):
    try:

        # Get brand profile belonging to this user
        brand_data = brand_repository.get_profile(
            profile_id=request.brand_profile_id,
            user_id=request.user_id
        )

        if not brand_data:
            raise HTTPException(
                status_code=404,
                detail="Brand profile not found for this user"
            )

        profile_row = brand_data[0]
        material_count = brand_dna_service.corpus_item_count(
            request.brand_profile_id,
            request.user_id,
        )
        setup_status = derive_setup_status(profile_row, material_count)
        if setup_status != "ready_to_draft":
            raise HTTPException(
                status_code=400,
                detail=user_safe_not_ready_message(setup_status),
            )

        brand_profile = BrandProfile(
            **profile_row
        )

        result = await social_content_workflow.generate(
            topic=request.topic,
            description=request.description,
            platform=request.platform,

            brand_profile=brand_profile,

            user_id=request.user_id,
            brand_profile_id=request.brand_profile_id,

            social_account_id=None
        )

        return result

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

