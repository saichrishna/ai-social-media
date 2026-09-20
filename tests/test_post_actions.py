from services.post_actions import allowed_actions


def test_allowed_actions_draft():

    assert allowed_actions("draft") == [
        "edit",
        "regenerate",
        "approve",
    ]


def test_allowed_actions_approved():

    assert allowed_actions("approved") == [
        "edit",
        "regenerate",
        "schedule",
    ]


def test_allowed_actions_scheduled_blocks_approve():

    assert allowed_actions("scheduled") == [
        "edit",
        "regenerate",
    ]


def test_allowed_actions_failed_allows_approve():

    assert "approve" in allowed_actions("failed")
