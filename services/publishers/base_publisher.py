from abc import ABC, abstractmethod


class BasePublisher(ABC):

    @abstractmethod
    async def publish(
        self,
        post: dict
    ) -> dict:
        """
        Publish a social media post.

        Expected response:

        {
            "success": True,
            "external_post_id": "..."
        }

        OR

        {
            "success": False,
            "error": "..."
        }
        """

        pass