from pydantic import BaseModel


class VoiceSampleRequest(BaseModel):

    # user_id lives on query and/or body (social-account style).
    # brand_profile_id lives on the path.

    user_id: str = ""

    source: str

    content: str
