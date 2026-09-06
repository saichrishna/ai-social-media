from models.brand_profile import BrandProfile


def build_brand_context(
    brand_profile: BrandProfile | None
) -> str:

    if not brand_profile:
        return ""

    return f"""
BUSINESS NAME:
{brand_profile.business_name}

INDUSTRY:
{brand_profile.industry}

LOCATION:
{brand_profile.location}

BRAND VOICE:
{brand_profile.brand_voice}

TARGET AUDIENCE:
{brand_profile.target_audience}

SERVICES:
{", ".join(brand_profile.services)}

PREFERRED HASHTAGS:
{", ".join(brand_profile.preferred_hashtags)}

FORBIDDEN TOPICS:
{", ".join(brand_profile.forbidden_topics)}

ADDITIONAL INSTRUCTIONS:
{brand_profile.additional_instructions}
""".strip()