from services.interview_plans import build_mini_session_plan


def test_build_mini_session_plan_has_two_questions():

    plan = build_mini_session_plan(
        {"business_name": "Clinic"},
        "Founders who hate jargon",
    )

    assert len(plan["questions"]) == 2
    assert plan["questions"][0]["question_key"] == "unpublished_advice"
    assert "Founders" in plan["prep_brief"]
