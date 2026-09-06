from agents.content_strategist import ContentStrategist
from agents.prompt_engineer import PromptEngineer
from agents.content_generator import ContentGenerator
from agents.content_reviewer import ContentReviewer

from models.brand_profile import BrandProfile


class SocialContentWorkflow:

    def __init__(self):
        self.content_strategist = ContentStrategist()
        self.prompt_engineer = PromptEngineer()
        self.content_generator = ContentGenerator()
        self.content_reviewer = ContentReviewer()

    # -----------------------------------
    # BUILD BRAND CONTEXT
    # -----------------------------------

    def build_brand_context(
        self,
        brand_profile: BrandProfile | None
    ) -> str:

        if not brand_profile:
            return ""

        return f"""
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
    # GENERATE CONTENT STRATEGY + TOPICS
    # -----------------------------------

    async def generate_topics(
        self,
        question: str = "",
        platform: str = "instagram",
        brand_profile: BrandProfile | None = None,
        number_of_topics: int = 5,
        business_goal: str = ""
    ) -> dict:

        brand_context = self.build_brand_context(
            brand_profile
        )

        strategy_result = await self.content_strategist.generate_topics(
            question=question,
            platform=platform,
            brand_context=brand_context,
            number_of_topics=number_of_topics,
            business_goal=business_goal
        )

        return {
            "success": True,

            "brand": (
                brand_profile.model_dump()
                if brand_profile
                else None
            ),

            "platform": platform,

            "strategy": strategy_result.get(
                "strategy",
                {}
            ),

            "topics": strategy_result.get(
                "topics",
                []
            ),

            "error": strategy_result.get(
                "error"
            )
        }

    # -----------------------------------
    # GENERATE SOCIAL MEDIA CONTENT
    # -----------------------------------

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

        brand_context = self.build_brand_context(
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

                if improved_caption and improved_caption.strip():

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

The previous generated content did not pass quality review.

ISSUES:
{issues}

SUGGESTIONS:
{suggestions}

Generate a completely improved version.

Avoid repeating the same mistakes.

Follow all brand information strictly.
"""

            content_prompt += improvement_feedback

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