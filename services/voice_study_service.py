import json

from services.ollama_service import OllamaService
from services.brand_dna_service import BrandDnaService


class VoiceStudyService:

    def __init__(self):
        self.llm = OllamaService()
        self.brand_dna = BrandDnaService()

    async def run_study(
        self,
        brand_profile_id: str,
        user_id: str,
        brand_profile: dict
    ) -> dict:

        corpus = self.brand_dna.gather_corpus(
            brand_profile_id,
            user_id
        )

        if len(corpus) < 3:
            raise ValueError(
                "Need at least three pastes or answers before voice study."
            )

        joined = "\n\n---\n\n".join(corpus)

        system_prompt = """
You analyze how a person writes or speaks from their own words only.
Return valid JSON. Do not invent traits not evidenced in the text.
""".strip()

        user_prompt = f"""
Corpus (user-provided only):

{joined}

Return JSON:
{{
  "keep_items": ["short observable patterns to preserve"],
  "raise_items": ["specific improvements while keeping their voice"],
  "source_summary": "one sentence on what material you used"
}}

KEEP examples: sentence openings, I/we usage, humor, emoji, length, slang.
RAISE examples: weak opener, buried point, jargon they use under pressure.
Max 8 items per list. Quote lightly when helpful.
""".strip()

        raw = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            json_format=True
        )

        parsed = json.loads(raw)

        keep_items = [
            str(item).strip()
            for item in (parsed.get("keep_items") or [])
            if str(item).strip()
        ][:8]

        raise_items = [
            str(item).strip()
            for item in (parsed.get("raise_items") or [])
            if str(item).strip()
        ][:8]

        return {
            "keep_items": keep_items,
            "raise_items": raise_items,
            "source_summary": str(
                parsed.get("source_summary") or ""
            ).strip()
        }
