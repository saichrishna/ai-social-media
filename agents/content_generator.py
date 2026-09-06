import json

from services.ollama_service import OllamaService

class ContentGenerator:
    def __init__(self):
        self.llm = OllamaService()

    async def generate_content(
        self,
        prompt: str,
        platform: str = "instagram",
        brand_context: str = ""
    ) -> dict:

        platform_rules = self._get_platform_rules(platform)

        system_prompt = f"""
    ```

    You are an expert Social Media Content Creator.

    Generate high-quality, engaging social media content
    based on the provided content brief and brand information.

    Adapt the content specifically for the requested platform.

    ========================================
    PLATFORM-SPECIFIC RULES
    =======================

    {platform_rules}

    ========================================
    REQUIRED OUTPUT
    ===============

    Your response must contain:

    * headline
    * caption
    * hashtags
    * call_to_action
    * image_prompt

    ========================================
    CRITICAL FACTUAL ACCURACY RULES
    ===============================

    1. Do NOT invent businesses, gym names, people, addresses,
       statistics, testimonials, locations, social media handles,
       websites, discounts, offers, or factual claims.

    2. Only mention business services that are explicitly provided
       in the brand information.

    3. If specific businesses, locations, social media handles,
       or factual details are not provided, use generic wording.

    ========================================
    CRITICAL OUTPUT RULES
    =====================

    4. Do NOT include hashtags inside the caption.

    5. Return all hashtags ONLY inside the hashtags array.

    6. Do NOT use Markdown formatting.

    7. Do NOT use:

    * bold
    * underline
    * Markdown headings
    * asterisks for emphasis

    8. The caption must be ready to directly publish on the
       requested social media platform.

    9. Do not repeat the call to action excessively.

    10. Keep image_prompt separate from the caption.

    11. Follow the provided brand voice strictly.

    12. Respect forbidden topics and additional instructions.

    13. Use only preferred hashtags provided in the brand information
        when they are relevant, but you may add other relevant hashtags.

    14. Do NOT invent branded hashtags.

    15. The content must sound natural for the selected platform.

    16. Do NOT invent business promotions or offers.

Never invent:

- discounts
- limited-time offers
- membership prices
- special deals
- free trials
- giveaways
- contests
- events

unless explicitly provided in the brand information.

17. Do NOT invent services.

Do not assume services such as:

- personal training
- 1:1 coaching
- nutrition coaching
- group classes
- online coaching

unless explicitly listed in the brand information.

18. Do NOT assume the business has specific people,
facilities, equipment, videos, photos, testimonials,
or members available.

If suggesting behind-the-scenes or visual content,
describe it conditionally or generically.
    Return ONLY valid JSON.

    Use exactly this structure:

    {{
    "headline": "Short engaging headline",
    "caption": "Full social media caption without hashtags",
    "hashtags": [
    "#example",
    "#example2"
    ],
    "call_to_action": "Call to action",
    "image_prompt": "Detailed prompt for generating an image"
    }}
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
    CONTENT BRIEF
    =============

    {prompt}
    """

        response = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            json_format=True
        )

        return json.loads(response)

    def _get_platform_rules(self, platform: str) -> str:

        platform = platform.lower().strip()

        if platform == "instagram":
            return """
    ```

    INSTAGRAM RULES:

    * Make the content visually engaging.
    * Use a strong hook in the first sentence.
    * Use short paragraphs for mobile readability.
    * Emojis are encouraged when appropriate.
    * Keep the tone engaging and energetic.
    * Use approximately 5 to 12 relevant hashtags.
    * Encourage comments, saves, shares, or engagement.
    * The image_prompt should describe a visually strong social media image.
      """

        elif platform == "linkedin":
            return """
      ```

    LINKEDIN RULES:

    * Use a professional and credible tone.
    * Focus on insights, expertise, lessons, or industry value.
    * Avoid excessive emojis.
    * Use short paragraphs for readability.
    * Avoid overly promotional language unless appropriate.
    * Use approximately 3 to 5 relevant hashtags.
    * Encourage professional discussion.
    * The image_prompt should describe a professional, credible visual.
      """

        elif platform == "facebook":
            return """
      ```

    FACEBOOK RULES:

    * Use a conversational and friendly tone.
    * Make the content easy to read.
    * Encourage comments and community interaction.
    * Use approximately 2 to 5 relevant hashtags.
    * Emojis may be used naturally.
    * Avoid excessive hashtags.
    * The image_prompt should describe a relatable and engaging visual.
      """

        elif platform in ["x", "twitter"]:
            return """
      ```

    X (TWITTER) RULES:

    * Keep the content concise and impactful.
    * Prioritize a strong opinion, insight, or hook.
    * Keep the caption within approximately 280 characters when possible.
    * Use minimal emojis.
    * Use approximately 1 to 3 hashtags.
    * Avoid unnecessary explanations.
    * The image_prompt should describe a simple, high-impact visual.
      """

        elif platform == "threads":
            return """
      ```

    THREADS RULES:

    * Use a conversational and authentic tone.
    * Write like a person starting a discussion.
    * Encourage replies and conversation.
    * Avoid sounding overly corporate.
    * Use approximately 0 to 3 hashtags.
    * The caption can include a question or opinion.
    * The image_prompt should support the conversation naturally.
      """

        else:
            return """
      ```

    GENERAL SOCIAL MEDIA RULES:

    * Create engaging and easy-to-read content.
    * Use the brand voice consistently.
    * Use hashtags naturally and appropriately.
    * Adapt the content for general social media audiences.
    * Keep the image_prompt visually relevant.
      """
