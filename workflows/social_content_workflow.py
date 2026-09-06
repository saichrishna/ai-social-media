from agents.prompt_engineer import PromptEngineer
from agents.content_generator import ContentGenerator
from agents.content_reviewer import ContentReviewer

from models.brand_profile import BrandProfile
from utils.brand_context import build_brand_context


class SocialContentWorkflow:

    def __init__(self):
        self.prompt_engineer = PromptEngineer()
        self.content_generator = ContentGenerator()
        self.content_reviewer = ContentReviewer()

    async def generate(
        self,
        topic: str,
        description: str = "",
        platform: str = "instagram",
        brand_profile: BrandProfile | None = None,
        max_attempts: int = 3
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

                    status = "approved_with_improvements"

                else:
                    status = "approved"

                return {
                    "success": True,
                    "status": status,
                    "attempt": attempt,

                    "brand": (
                        brand_profile.model_dump()
                        if brand_profile
                        else None
                    ),

                    "prompt_engineering": prompt_result,

                    "content": content,

                    "review": review,

                    "attempt_history": attempts
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