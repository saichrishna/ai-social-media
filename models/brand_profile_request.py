from pydantic import BaseModel, Field
from typing import List


class BrandProfileRequest(BaseModel):

    user_id: str

    business_name: str

    industry: str

    location: str = ""

    brand_voice: str = ""

    target_audience: str = ""

    services: List[str] = Field(default_factory=list)

    preferred_hashtags: List[str] = Field(default_factory=list)

    forbidden_topics: List[str] = Field(default_factory=list)

    additional_instructions: str = ""