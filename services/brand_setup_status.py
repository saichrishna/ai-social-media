from __future__ import annotations

from collections import defaultdict
from typing import Literal

from utils.promise_completeness import promise_warnings

BrandSetupStatus = Literal[
    "promise_incomplete",
    "need_your_words",
    "ready_to_draft",
]

MIN_MATERIAL_ITEMS = 3


def promise_is_complete(profile: dict) -> bool:
    warnings = promise_warnings(profile)
    if warnings:
        return False
    target = str(profile.get("target_audience") or "").strip()
    not_for = str(profile.get("not_for") or "").strip()
    return bool(target and not_for)


def count_material_row(content: str | None) -> bool:
    return bool((content or "").strip())


def material_counts_from_rows(
    samples: list[dict],
    answers: list[dict],
) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)

    for row in samples:
        profile_id = row.get("brand_profile_id")
        if not profile_id:
            continue
        if count_material_row(row.get("content")):
            counts[str(profile_id)] += 1

    for row in answers:
        profile_id = row.get("brand_profile_id")
        if not profile_id:
            continue
        if count_material_row(row.get("answer_text")):
            counts[str(profile_id)] += 1

    return dict(counts)


def derive_setup_status(
    profile: dict,
    material_count: int,
) -> BrandSetupStatus:
    if not promise_is_complete(profile):
        return "promise_incomplete"
    if material_count < MIN_MATERIAL_ITEMS:
        return "need_your_words"
    return "ready_to_draft"


def enrich_profile_with_setup(
    profile: dict,
    material_count: int,
) -> dict:
    setup_status = derive_setup_status(profile, material_count)
    return {
        **profile,
        "promise_complete": promise_is_complete(profile),
        "material_count": material_count,
        "setup_status": setup_status,
        "draft_ready": setup_status == "ready_to_draft",
    }


def user_safe_not_ready_message(setup_status: BrandSetupStatus) -> str:
    if setup_status == "promise_incomplete":
        return (
            "Finish your brand promise first — who you help and who you are not for."
        )
    if setup_status == "need_your_words":
        return (
            "Add at least three pastes or answers in Your words before drafting."
        )
    return "Brand is not ready to generate content."
