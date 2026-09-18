import os
from urllib.parse import urlencode

from services.social_providers.base_provider import (
    BaseSocialProvider
)


class InstagramProvider(BaseSocialProvider):

    def __init__(self):

        self.client_id = os.getenv(
            "INSTAGRAM_CLIENT_ID"
        )

        self.client_secret = os.getenv(
            "INSTAGRAM_CLIENT_SECRET"
        )

        self.redirect_uri = os.getenv(
            "INSTAGRAM_REDIRECT_URI"
        )


    # -----------------------------------
    # GET AUTHORIZATION URL
    # -----------------------------------

    def get_authorization_url(
        self,
        state: str
    ) -> str:

        params = {

            "client_id": self.client_id,

            "redirect_uri": self.redirect_uri,

            "response_type": "code",

            "scope": (
                "instagram_business_basic,"
                "instagram_business_content_publish"
            ),

            "state": state
        }

        query = urlencode(params)

        return (
            "https://www.instagram.com/oauth/authorize"
            f"?{query}"
        )


    # -----------------------------------
    # EXCHANGE CODE
    # -----------------------------------

    async def exchange_code(
        self,
        code: str
    ) -> dict:

        raise NotImplementedError(
            "Instagram OAuth token exchange "
            "not implemented yet"
        )


    # -----------------------------------
    # GET VERIFIED ACCOUNTS
    # -----------------------------------

    async def get_accounts(
        self,
        access_token: str
    ) -> list:

        raise NotImplementedError(
            "Instagram account retrieval "
            "not implemented yet"
        )


    # -----------------------------------
    # PUBLISH
    # -----------------------------------

    async def publish(
        self,
        post: dict,
        account: dict
    ) -> dict:

        raise NotImplementedError(
            "Instagram publishing "
            "not implemented yet"
        )