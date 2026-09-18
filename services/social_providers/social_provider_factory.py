from services.social_providers.instagram_provider import (
    InstagramProvider
)


class SocialProviderFactory:

    @staticmethod
    def get_provider(
        platform: str
    ):

        platform = platform.lower()

        providers = {

            "instagram": InstagramProvider

        }

        provider_class = providers.get(
            platform
        )

        if not provider_class:

            raise ValueError(
                f"Unsupported platform: {platform}"
            )

        return provider_class()