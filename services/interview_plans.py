def build_mini_session_plan(
    brand_profile: dict,
    cold_open_answer: str = "",
) -> dict:
    name = brand_profile.get("business_name") or "your brand"
    seed = (cold_open_answer or "").strip()
    brief = (
        f"Quick capture for {name}. "
        "One or two things only you would say — we add them to your corpus."
    )
    if seed:
        brief = f"{brief} You mentioned: {seed[:200]}"

    questions = [
        {
            "question_key": "unpublished_advice",
            "question_text": (
                "What's on your mind right now that you'd want on the feed?"
            ),
            "answer_text": "",
            "source": "",
            "answered": False,
        },
        {
            "question_key": "customer_sentence",
            "question_text": (
                "Anything else this week — a line a customer said or advice you give?"
            ),
            "answer_text": "",
            "source": "",
            "answered": False,
        },
    ]

    return {
        "prep_brief": brief,
        "questions": questions,
    }
