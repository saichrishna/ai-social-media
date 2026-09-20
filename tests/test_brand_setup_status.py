from services.brand_setup_status import (
    derive_setup_status,
    enrich_profile_with_setup,
    material_counts_from_rows,
    promise_is_complete,
)


def test_promise_is_complete_requires_both_fields():

    assert promise_is_complete({
        "target_audience": "Founders",
        "not_for": "Enterprise only",
    })
    assert not promise_is_complete({
        "target_audience": "Founders",
        "not_for": "",
    })


def test_material_counts_from_rows():

    counts = material_counts_from_rows(
        [
            {
                "brand_profile_id": "b1",
                "content": "  hello ",
            },
            {
                "brand_profile_id": "b1",
                "content": "",
            },
        ],
        [
            {
                "brand_profile_id": "b1",
                "answer_text": "answer",
            },
            {
                "brand_profile_id": "b2",
                "answer_text": "other",
            },
        ],
    )

    assert counts == {"b1": 2, "b2": 1}


def test_derive_setup_status_flow():

    profile = {
        "target_audience": "Founders",
        "not_for": "Kids",
    }

    assert derive_setup_status(profile, 0) == "need_your_words"
    assert derive_setup_status(profile, 2) == "need_your_words"
    assert derive_setup_status(profile, 3) == "ready_to_draft"
    assert derive_setup_status(
        {"target_audience": "", "not_for": ""},
        10,
    ) == "promise_incomplete"


def test_enrich_profile_with_setup():

    enriched = enrich_profile_with_setup(
        {
            "id": "b1",
            "target_audience": "Founders",
            "not_for": "Kids",
        },
        3,
    )

    assert enriched["setup_status"] == "ready_to_draft"
    assert enriched["draft_ready"] is True
    assert enriched["material_count"] == 3
    assert enriched["promise_complete"] is True
