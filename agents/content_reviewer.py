import json

from services.ollama_service import OllamaService

class ContentReviewer:
    def __init__(self):
        self.llm = OllamaService()

    async def review_content(
        self,
        headline: str,
        caption: str,
        hashtags: list,
        call_to_action: str,
        platform: str = "instagram",
        brand_context: str = ""
    ) -> dict:

        platform_rules = self._get_platform_rules(platform)

        system_prompt = f"""
    ```

    You are a strict Social Media Content Quality Reviewer.

    Review the provided social media content carefully.

    ========================================
    PLATFORM-SPECIFIC REVIEW RULES
    ==============================

    {platform_rules}

    ========================================
    EVALUATION CRITERIA
    ===================

    Evaluate:

    1. Grammar and spelling
    2. Clarity and readability
    3. Engagement potential
    4. Platform suitability
    5. Quality of the call to action
    6. Relevance and quality of hashtags
    7. Duplicate or unnecessary content
    8. Whether the content feels natural and human-written
    9. Brand voice consistency
    10. Compliance with forbidden topics
    11. Accuracy of services mentioned
    12. Whether facts, locations, businesses, handles, or statistics
        have been invented

    ========================================
    BRAND COMPLIANCE
    ================

    You must verify that the content follows the provided
    brand information.

    Flag or reject content that:

    * Violates forbidden topics
    * Uses the wrong brand voice
    * Targets the wrong audience
    * Promotes services the business does not offer
    * Invents businesses, facts, locations, statistics, testimonials,
      social media handles, websites, discounts, or offers
    * Uses hashtags that falsely imply affiliation
    * Ignores important brand instructions

    ========================================
    SCORING
    =======

    Give each area a score from 0 to 100.

    IMPORTANT:

    Approve content only if the overall quality is good enough
    to be published automatically.

    Do not give artificially high scores.

    A score of 90+ means excellent and publication-ready.

    A score of 80-89 means good, but minor improvements may be useful.

    A score below 80 means the content should not be automatically published.

    ========================================
    OUTPUT RULES
    ============

    Return ONLY valid JSON.

    Use exactly this structure:

    {{
    "approved": true,
    "overall_score": 90,
    "grammar_score": 95,
    "clarity_score": 90,
    "engagement_score": 88,
    "platform_score": 92,
    "cta_score": 90,
    "hashtag_score": 85,
    "issues": [],
    "suggestions": [],
    "improved_caption": "",
    "reason": "Short explanation of the decision"
    }}

    ========================================
    DECISION RULES
    ==============

    * approved must be true only if overall_score >= 80.
    * If there are serious factual or brand violations,
      approved must be false.
    * Serious violations must NOT receive an overall score >= 80.
    * Identify duplicate hashtags.
    * Identify hashtags repeated unnecessarily in the caption.
    * Identify unnecessary repetition.
    * Check whether the CTA matches the selected platform.
    * Give practical and actionable suggestions.
    * Only provide improved_caption if meaningful improvements
      are actually needed.
    * If the content is already excellent, improved_caption
      should be an empty string.
    * Do NOT invent improvements involving businesses, locations,
      social media handles, statistics, or services.
      """


        user_prompt = f"""
      ```

    ========================================
    BRAND INFORMATION
    =================

    {brand_context}

    ========================================
    PLATFORM
    ========

    {platform}

    ========================================
    HEADLINE
    ========

    {headline}

    ========================================
    CAPTION
    =======

    {caption}

    ========================================
    HASHTAGS
    ========

    {json.dumps(hashtags)}

    ========================================
    CALL TO ACTION
    ==============

    {call_to_action}
    """

        response = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            json_format=True
        )

        return json.loads(response)

    def _get_platform_rules(self, platform: str) -> str:

        platform = platform.lower().strip()

        if platform == "instagram":
            return """
    ```

    INSTAGRAM REVIEW RULES:

    * Check that the opening is engaging.
    * Check mobile readability and paragraph structure.
    * Emojis may be used naturally but should not be excessive.
    * Check that the content encourages engagement where appropriate.
    * Ideal hashtag range is approximately 5 to 12.
    * The content should feel visually engaging.
    * Do not require hashtags inside the caption.
      """

        elif platform == "linkedin":
            return """
      ```

    LINKEDIN REVIEW RULES:

    * Check for professional and credible language.
    * Evaluate whether the content provides insight or value.
    * Avoid excessive emojis.
    * Avoid overly aggressive promotional language unless it matches
      the brand voice.
    * Ideal hashtag range is approximately 3 to 5.
    * Check that the CTA encourages meaningful professional discussion.
      """


        elif platform == "facebook":
            return """
      ```

    FACEBOOK REVIEW RULES:

    * Check that the tone is conversational and community-friendly.
    * Evaluate readability for a general audience.
    * Check that the CTA encourages interaction.
    * Ideal hashtag range is approximately 2 to 5.
    * Avoid excessive promotional language unless appropriate.
      """

        elif platform in ["x", "twitter"]:
            return """
      ```

    X (TWITTER) REVIEW RULES:

    * Check that the content is concise and impactful.
    * Prefer captions around 280 characters when reasonably possible.
    * Evaluate the strength of the opening statement.
    * Avoid unnecessary explanations.
    * Ideal hashtag range is approximately 1 to 3.
    * Check that the CTA is concise.
      """

        elif platform == "threads":
            return """
      ```

    THREADS REVIEW RULES:

    * Check that the tone feels conversational and authentic.
    * Avoid overly corporate language unless required by the brand.
    * Encourage replies or discussion where appropriate.
    * Ideal hashtag range is approximately 0 to 3.
    * Check that the content feels natural and human.
      """

        else:
            return """
      ```

    GENERAL SOCIAL MEDIA REVIEW RULES:

    * Evaluate readability and engagement.
    * Ensure the content follows the brand voice.
    * Ensure hashtags are relevant and not excessive.
    * Ensure the CTA is natural and useful.
      """
