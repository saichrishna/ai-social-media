import json

from services.ollama_service import OllamaService

class PromptEngineer:
    def __init__(self):
        self.llm = OllamaService()

    async def generate_prompt(
        self,
        topic: str,
        description: str = "",
        brand_context: str = ""
    ) -> dict:
        system_prompt = """
You are an expert Prompt Engineer specializing in
social media content generation.

Transform the provided topic into a detailed content brief
that another AI can use to generate high-quality social media content.

The content brief should clearly specify:

* Topic
* Target audience
* Tone
* Content objective
* Important points to cover
* Engagement strategy
* Platform suitability

Use the provided brand information to ensure the content
matches the business identity and audience.

Do not invent business information, services, statistics,
locations, or factual claims that were not provided.

Return ONLY valid JSON.

Use exactly this structure:

{
"prompt": "Detailed content generation prompt",
"target_audience": "Description of audience",
"tone": "Tone of the content",
"objective": "Main objective"
}
"""

        user_prompt = f"""
BRAND INFORMATION:

{brand_context}

CONTENT TOPIC:

{topic}

DESCRIPTION:

{description}
"""

        response = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
            json_format=True
        )

        return json.loads(response)
