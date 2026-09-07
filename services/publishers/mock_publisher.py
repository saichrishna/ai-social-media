import asyncio
import uuid

from services.publishers.base_publisher import (
    BasePublisher
)


class MockPublisher(BasePublisher):

    async def publish(
        self,
        post: dict
    ) -> dict:

        print(
            f"Mock publishing post "
            f"{post['id']} "
            f"to {post['platform']}"
        )

        # Simulate API processing
        await asyncio.sleep(2)

        external_post_id = str(
            uuid.uuid4()
        )

        return {
            "success": True,
            "external_post_id": external_post_id
        }