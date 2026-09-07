from abc import ABC, abstractmethod


class BasePublisher(ABC):

    @abstractmethod
    async def publish(self, post: dict):
        pass


class InstagramPublisher(BasePublisher):

    async def publish(self, post: dict):

        print("Publishing to Instagram...")

        # Temporary implementation
        return {
            "success": True,
            "platform": "instagram",
            "external_post_id": "demo_instagram_post_id"
        }


class LinkedInPublisher(BasePublisher):

    async def publish(self, post: dict):

        print("Publishing to LinkedIn...")

        # Temporary implementation
        return {
            "success": True,
            "platform": "linkedin",
            "external_post_id": "demo_linkedin_post_id"
        }


class FacebookPublisher(BasePublisher):

    async def publish(self, post: dict):

        print("Publishing to Facebook...")

        # Temporary implementation
        return {
            "success": True,
            "platform": "facebook",
            "external_post_id": "demo_facebook_post_id"
        }


class PublisherFactory:

    @staticmethod
    def get_publisher(platform: str):

        platform = platform.lower()

        publishers = {
            "instagram": InstagramPublisher,
            "linkedin": LinkedInPublisher,
            "facebook": FacebookPublisher
        }

        publisher_class = publishers.get(platform)

        if not publisher_class:
            raise ValueError(
                f"Unsupported platform: {platform}"
            )

        return publisher_class()