def promise_warnings(profile: dict) -> list[str]:

    warnings = []

    target_audience = str(
        profile.get("target_audience") or ""
    )

    not_for = str(
        profile.get("not_for") or ""
    )

    if not target_audience.strip():
        warnings.append("target_audience is empty")

    if not not_for.strip():
        warnings.append("not_for is empty")

    return warnings
