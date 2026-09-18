from services.social_providers.base_provider import (
    BaseSocialProvider
)


class LinkedInProvider(BaseSocialProvider):

    def get_authorization_url(
        self,
        state: str
    ) -> str:

        raise NotImplementedError(
            "LinkedIn OAuth not implemented yet"
        )


    async def exchange_code(
        self,
        code: str
    ) -> dict:

        raise NotImplementedError(
            "LinkedIn OAuth not implemented yet"
        )


    async def get_accounts(
        self,
        access_token: str
    ) -> list:

        raise NotImplementedError(
            "LinkedIn account retrieval not implemented yet"
        )


    async def publish(
        self,
        account: dict,
        post: dict
    ) -> dict:

        raise NotImplementedError(
            "LinkedIn publishing not implemented yet"
        )