import json

from services.ollama_service import OllamaService


class ContentStrategist:

    def __init__(self):
        self.llm = OllamaService()

    async def generate_topics(
        self,
        question: str = "",
        platform: str = "instagram",
        brand_context: str = "",
        number_of_topics: int = 5,
        business_goal: str = ""
    ) -> dict:

        system_prompt = f"""
You are an expert Social Media Content Strategist.

Your job is to create a content strategy and generate
high-quality social media content topics.

You must consider:

- Business information
- Industry
- Target audience
- Brand voice
- Business services
- Preferred hashtags
- Forbidden topics
- Additional brand instructions
- Platform
- Business goal
- User's requested topic or question

Generate exactly {number_of_topics} content ideas.

IMPORTANT STRATEGY RULES:

1. Topics must be relevant to the business.

2. Topics must target the specified audience.

3. Follow the brand voice strictly.

4. Only promote services explicitly mentioned in the
brand information.

5. Strictly avoid forbidden topics.

6. Do NOT invent:

- businesses
- business names
- gym names
- addresses
- statistics
- testimonials
- people
- events
- locations
- partnerships
- awards
- certifications
- facilities
- equipment

7. Do NOT invent business promotions or offers.

Never invent:

- discounts
- limited-time offers
- membership prices
- special deals
- free trials
- giveaways
- contests

unless explicitly provided in the brand information.

8. Do NOT invent services.

Do not assume services such as:

- personal training
- 1:1 coaching
- nutrition coaching
- group classes
- online coaching

unless explicitly listed in the brand information.

9. Do NOT assume the business has specific people,
facilities, equipment, videos, photos, testimonials,
members, trainers, or content assets available.

For example, do NOT assume:

- a trainer is available for filming
- members can appear in videos
- customer testimonials exist
- specific equipment is available

unless explicitly provided in the brand information.

10. Generate a balanced variety of content types.

Allowed content types:

- educational
- promotional
- engaging
- informative
- motivational
- trending
- behind_the_scenes

IMPORTANT:

Only use "promotional" topics to promote services
explicitly listed in the brand information.

Do not invent promotional offers.

11. Avoid duplicate or very similar topics.

12. Each topic must have a clear strategic reason.

13. If brand information is missing, do not invent
business-specific facts.

Use generic and safe content ideas instead.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "strategy": {{
        "primary_goal": "Main business goal",
        "target_audience": "Target audience",
        "content_pillars": [
            {{
                "name": "Pillar name",
                "description": "What this pillar focuses on"
            }}
        ],
        "recommended_content_mix": {{
            "educational": 40,
            "motivational": 20,
            "engaging": 20,
            "promotional": 20
        }}
    }},

    "topics": [
        {{
            "title": "Topic title",
            "description": "Short explanation of the topic",
            "content_type": "educational",
            "content_pillar": "Related pillar",
            "strategic_reason": "Why this topic helps the business"
        }}
    ]
}}
"""

        user_prompt = f"""
BRAND INFORMATION:

{brand_context if brand_context else "No brand profile provided."}

PLATFORM:

{platform}

BUSINESS GOAL:

{business_goal if business_goal else "Increase engagement and support business growth."}

USER REQUEST:

{question if question else "Generate the best content topics based on the brand strategy."}

NUMBER OF TOPICS:

{number_of_topics}
"""

        response = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            json_format=True
        )

        cleaned_response = response.strip()

        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response.replace(
                "```json",
                "",
                1
            )

        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace(
                "```",
                "",
                1
            )

        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        try:
            return json.loads(cleaned_response.strip())

        except json.JSONDecodeError:

            return {
                "strategy": {},
                "topics": [],
                "raw_response": response,
                "error": "Ollama did not return valid JSON"
            }