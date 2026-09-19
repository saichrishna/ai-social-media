from agents.prompt_engineer import PromptEngineer
from agents.content_generator import ContentGenerator
from agents.content_reviewer import ContentReviewer

from repositories.social_post_repository import SocialPostRepository
from models.brand_profile import BrandProfile
from utils.brand_context import build_brand_context

from services.media_generation_service import (
    MediaGenerationService
)
class SocialContentWorkflow:

    def __init__(self):
        self.prompt_engineer = PromptEngineer()
        self.content_generator = ContentGenerator()
        self.content_reviewer = ContentReviewer()
        self.social_post_repository = SocialPostRepository()
        self.media_generation = MediaGenerationService()
    async def generate(
        self,
        topic: str,
        description: str = "",
        platform: str = "instagram",
        brand_profile: BrandProfile | None = None,
        user_id: str | None = None,
        brand_profile_id: str | None = None,
        max_attempts: int = 3,
        social_account_id: str | None = None,
    ) -> dict:

        # -----------------------------------
        # BUILD BRAND CONTEXT
        # -----------------------------------

        brand_context = build_brand_context(
            brand_profile
        )

        # -----------------------------------
        # STEP 1: PROMPT ENGINEERING
        # -----------------------------------

        prompt_result = await self.prompt_engineer.generate_prompt(
            topic=topic,
            description=description,
            brand_context=brand_context
        )

        content_prompt = prompt_result["prompt"]

        attempts = []

        content = None
        review = None

        # -----------------------------------
        # STEP 2–4: GENERATE + REVIEW LOOP
        # -----------------------------------

        for attempt in range(1, max_attempts + 1):

            # -----------------------------------
            # STEP 2: GENERATE CONTENT
            # -----------------------------------

            content = await self.content_generator.generate_content(
                prompt=content_prompt,
                platform=platform,
                brand_context=brand_context
            )

            # -----------------------------------
            # STEP 3: REVIEW CONTENT
            # -----------------------------------

            review = await self.content_reviewer.review_content(
                headline=content["headline"],
                caption=content["caption"],
                hashtags=content["hashtags"],
                call_to_action=content["call_to_action"],
                platform=platform,
                brand_context=brand_context
            )

            attempts.append({
                "attempt": attempt,
                "overall_score": review.get("overall_score"),
                "approved": review.get("approved"),
                "issues": review.get("issues", [])
            })

            # -----------------------------------
            # STEP 4: APPROVED
            # -----------------------------------

            if review.get("approved"):

                improved_caption = review.get(
                    "improved_caption",
                    ""
                )

                if (
                    improved_caption
                    and improved_caption.strip()
                ):
                    content["caption"] = improved_caption

                status = "approved"

                # -----------------------------------
                # SAVE TO SUPABASE
                # -----------------------------------

                post_data = {
                    "user_id": user_id,
                    "brand_profile_id": brand_profile_id,
                    "social_account_id": social_account_id,
                    "topic": topic,
                    "description": description,

                    "headline": content.get("headline"),
                    "caption": content.get("caption"),
                    "hashtags": content.get("hashtags", []),
                    "call_to_action": content.get("call_to_action"),
                    "image_prompt": content.get("image_prompt"),

                    "platform": platform,

                    "prompt_engineering": prompt_result,

                    "review": review,

                    "attempt_history": attempts,

                    "status": status
                }

                saved_post = (
                self.social_post_repository
                .create_post(post_data)
                )

                if not saved_post:
                    raise ValueError(
                        "Failed to save social post."
                    )

                post = saved_post[0]

                # -----------------------------------
                # GENERATE POST IMAGE
                # -----------------------------------

                image_result = None

                image_prompt = post.get("image_prompt")

                if image_prompt:
                
                    try:
                    
                        image_result = (
                            self.media_generation
                            .generate_post_image(
                                post_id=post["id"],
                                prompt=image_prompt
                            )
                        )

                        # -----------------------------------
                        # UPDATE POST WITH IMAGE PATH
                        # -----------------------------------

                        updated_post = (
                            self.social_post_repository
                            .update_post(
                                post["id"],
                                {
                                    "image_url": (
                                        image_result["storage_path"]
                                    )
                                }
                            )
                        )

                        if updated_post:
                            post = updated_post[0]

                    except Exception as image_error:
                    
                        # Image failure should NOT destroy
                        # an otherwise valid generated post.

                        image_result = {
                            "success": False,
                            "error": str(image_error)
                        }

                return {
                    "success": True,
                    "status": status,
                    "attempt": attempt,

                    "post": post,

                    "brand": (
                        brand_profile.model_dump()
                        if brand_profile
                        else None
                    ),

                    "prompt_engineering": prompt_result,

                    "content": content,

                    "review": review,

                    "attempt_history": attempts,

                    "image": image_result
                }

                
            # -----------------------------------
            # CONTENT FAILED REVIEW
            # -----------------------------------

            issues = review.get("issues", [])
            suggestions = review.get("suggestions", [])

            improvement_feedback = f"""

The previous generated content did not pass
quality review.

Issues:

{issues}

Suggestions:

{suggestions}

Generate a completely improved version.

Avoid repeating the same mistakes.

Follow all brand information strictly.

Do not invent:

- services
- offers
- discounts
- business facts
- locations
- statistics
- people
- testimonials
"""

            content_prompt = (
                content_prompt
                + improvement_feedback
            )

        # -----------------------------------
        # MAX ATTEMPTS REACHED
        # -----------------------------------

        return {
            "success": False,
            "status": "max_attempts_reached",

            "brand": (
                brand_profile.model_dump()
                if brand_profile
                else None
            ),

            "attempt_history": attempts,

            "last_content": content,

            "last_review": review
        }

    async def regenerate(self, post_id: str,brand_profile: BrandProfile,max_attempts: int = 3) -> dict:

        posts = self.social_post_repository.get_post(post_id)

        if not posts:
            raise ValueError("Social post not found")

        post = posts[0]

        topic = post.get("topic", "")
        description = post.get("description", "")
        platform = post.get("platform", "instagram")
        user_id = post.get("user_id")
        brand_profile_id = post.get("brand_profile_id")
        social_account_id = post.get("social_account_id")

        brand_context = build_brand_context(
            brand_profile
        )

        prompt_result = await self.prompt_engineer.generate_prompt(
            topic=topic,
            description=description,
            brand_context=brand_context
        )

        content_prompt = prompt_result["prompt"]

        attempts = []
        content = None
        review = None

        for attempt in range(1, max_attempts + 1):

            content = await self.content_generator.generate_content(
                prompt=content_prompt,
                platform=platform,
                brand_context=brand_context
            )

            review = await self.content_reviewer.review_content(
                headline=content["headline"],
                caption=content["caption"],
                hashtags=content["hashtags"],
                call_to_action=content["call_to_action"],
                platform=platform,
                brand_context=brand_context
            )

            attempts.append({
                "attempt": attempt,
                "overall_score": review.get("overall_score"),
                "approved": review.get("approved"),
                "issues": review.get("issues", [])
            })

            if review.get("approved"):

                improved_caption = review.get(
                    "improved_caption",
                    ""
                )

                if improved_caption and improved_caption.strip():
                    content["caption"] = improved_caption

                status = "draft"

                image_prompt = content.get(
                    "image_prompt"
                )

                update_data = {
                    "headline": content.get("headline"),
                    "caption": content.get("caption"),
                    "hashtags": content.get("hashtags", []),
                    "call_to_action": content.get(
                        "call_to_action"
                    ),
                    "image_prompt": image_prompt,
                    "platform": platform,
                    "prompt_engineering": prompt_result,
                    "review": review,
                    "attempt_history": attempts,
                    "status": status
                }

                updated_post = (
                    self.social_post_repository.update_post(
                        post_id=post_id,
                        post_data=update_data
                    )
                )

                image_result = None

                if image_prompt:
                    image_result = (
                        self.media_generation_service
                        .generate_post_image(
                            post_id=post_id,
                            prompt=image_prompt
                        )
                )

                image_update_result = (
                    self.social_post_repository.update_post(
                        post_id=post_id,
                        post_data={
                            "image_url": image_result["storage_path"]
                        }
                    )
                )

                if not image_update_result:
                    raise ValueError(
                        "Image was generated and uploaded, "
                        "but social post image_url was not updated."
                    )

                final_posts = (
                    self.social_post_repository
                    .get_post(post_id)
                )

                return {
                    "success": True,
                    "status": status,
                    "attempt": attempt,
                    "post": (
                        final_posts[0]
                        if final_posts
                        else None
                    ),
                    "brand": (
                        brand_profile.model_dump()
                    ),
                    "prompt_engineering": prompt_result,
                    "content": content,
                    "review": review,
                    "attempt_history": attempts,
                    "image": image_result
                }

            issues = review.get("issues", [])
            suggestions = review.get("suggestions", [])

            improvement_feedback = f"""

The previous generated content was rejected.

Issues:
{issues}

Suggestions:
{suggestions}

Generate a substantially improved version.
Do not repeat the same problems.
"""

            content_prompt = (
                content_prompt +
                improvement_feedback
            )

        return {
            "success": False,
            "status": "max_attempts_reached",
            "post_id": post_id,
            "attempt_history": attempts,
            "last_content": content,
            "last_review": review
        }    