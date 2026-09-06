from pydantic import BaseModel, Field

class BrandProfile(BaseModel):
    business_name: str
    industry: str
    location: str = ""
    brand_voice: str = "Professional and friendly"
    target_audience: str = ""
    services: list[str] = Field(default_factory=list)
    preferred_hashtags: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    additional_instructions: str = ""
