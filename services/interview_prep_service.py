import json

from services.ollama_service import OllamaService

CANONICAL_KEYS = [
    "customers_get_wrong",
    "changed_my_mind",
    "unpublished_advice",
    "customer_sentence",
    "industry_disagree",
]


class InterviewPrepService:

    def __init__(self):
        self.llm = OllamaService()

    async def build_session_plan(
        self,
        brand_profile: dict,
        cold_open_answer: str = ""
    ) -> dict:

        system_prompt = """
You prepare interview questions for a brand expert.
Use ONLY facts from the brand profile and cold open answer.
Do NOT invent customer quotes, reviews, or business history.
Return valid JSON only.
""".strip()

        user_prompt = f"""
Brand profile (JSON):
{json.dumps(brand_profile, ensure_ascii=False)}

Cold open (who they help, one breath):
{cold_open_answer or "(not provided yet)"}

Return JSON:
{{
  "prep_brief": "2-3 sentences explaining what you heard — no invented facts",
  "questions": [
    {{
      "question_key": "one of {CANONICAL_KEYS}",
      "question_text": "specific question for THIS business"
    }}
  ]
}}

Rules:
- Include 5 to 7 questions.
- Each question_key must be unique and from the allowed list.
- Questions must be specific, short, curious — not generic marketing.
- Do not use jargon like GTM or thought leadership.
""".strip()

        raw = await self.llm.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
            json_format=True
        )

        parsed = json.loads(raw)

        questions = parsed.get("questions") or []

        cleaned = []

        seen_keys = set()

        for item in questions:
            key = str(item.get("question_key", "")).strip()
            text = str(item.get("question_text", "")).strip()
            if key not in CANONICAL_KEYS or not text:
                continue
            if key in seen_keys:
                continue
            seen_keys.add(key)
            cleaned.append({
                "question_key": key,
                "question_text": text,
                "answer_text": "",
                "source": "",
                "answered": False
            })

        if len(cleaned) < 3:
            cleaned = self._fallback_questions(brand_profile)

        return {
            "prep_brief": str(
                parsed.get("prep_brief") or ""
            ).strip(),
            "questions": cleaned
        }

    def _fallback_questions(
        self,
        brand_profile: dict
    ) -> list[dict]:

        name = brand_profile.get(
            "business_name",
            "this business"
        )

        templates = {
            "customers_get_wrong": (
                f"What do people get wrong about {name}?"
            ),
            "changed_my_mind": (
                "What have you changed your mind about in this work?"
            ),
            "unpublished_advice": (
                "What advice do you give clients that you rarely post?"
            ),
            "customer_sentence": (
                "What is one sentence a real customer said about the problem?"
            ),
            "industry_disagree": (
                "What does your industry claim that you push back on?"
            ),
        }

        return [
            {
                "question_key": key,
                "question_text": templates[key],
                "answer_text": "",
                "source": "",
                "answered": False
            }
            for key in CANONICAL_KEYS
        ]
