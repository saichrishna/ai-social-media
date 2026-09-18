from services.social_providers.base_provider import (
    BaseSocialProvider
)


class FacebookProvider(BaseSocialProvider):

    def get_authorization_url(
        self,
        state: str
    ) -> str:

        raise NotImplementedError(
            "Facebook OAuth not implemented yet"
        )


    async def exchange_code(
        self,
        code: str
    ) -> dict:

        raise NotImplementedError(
            "Facebook OAuth not implemented yet"
        )


    async def get_accounts(
        self,
        access_token: str
    ) -> list:

        raise NotImplementedError(
            "Facebook account retrieval not implemented yet"
        )


    async def publish(
        self,
        account: dict,
        post: dict
    ) -> dict:

        raise NotImplementedError(
            "Facebook publishing not implemented yet"
        )