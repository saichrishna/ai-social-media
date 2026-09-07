from services.publishers.mock_publisher import (
    MockPublisher
)


class PublisherFactory:

    @staticmethod
    def get_publisher(platform: str):

        platform = platform.lower()

        # Temporary mock publishers

        if platform == "instagram":

            return MockPublisher()

        if platform == "linkedin":

            return MockPublisher()

        if platform == "facebook":

            return MockPublisher()

        raise ValueError(
            f"Unsupported platform: {platform}"
        )