import asyncio

from repositories.social_post_repository import (
    SocialPostRepository
)

from services.publisher_service import (
    PublisherFactory
)


class SchedulerService:

    def __init__(self):

        self.social_post_repository = (
            SocialPostRepository()
        )

        self.is_running = False


    async def process_due_posts(self):

        print("Checking for due posts...")

        try:

            due_posts = (
                self.social_post_repository
                .get_due_posts()
            )

            if not due_posts:

                print("No posts ready for publishing")

                return

            print(
                f"Found {len(due_posts)} "
                f"posts ready for publishing"
            )

            for post in due_posts:

                post_id = post["id"]

                try:

                    # -------------------------
                    # MARK AS PUBLISHING
                    # -------------------------

                    self.social_post_repository.update_post_status(
                        post_id=post_id,
                        status="publishing"
                    )

                    print(
                        f"Publishing post: {post_id}"
                    )

                    # -------------------------
                    # GET PLATFORM PUBLISHER
                    # -------------------------

                    publisher = (
                        PublisherFactory.get_publisher(
                            post["platform"]
                        )
                    )

                    # -------------------------
                    # PUBLISH
                    # -------------------------

                    result = await publisher.publish(post)

                    # -------------------------
                    # SUCCESS
                    # -------------------------

                    if result.get("success"):

                        self.social_post_repository.mark_post_published(

                            post_id=post_id,

                            external_post_id=(
                                result.get(
                                    "external_post_id"
                                )
                            )
                        )

                        print(
                            f"Post published successfully: "
                            f"{post_id}"
                        )

                    # -------------------------
                    # FAILURE
                    # -------------------------

                    else:

                        self.social_post_repository.update_post_status(

                            post_id=post_id,

                            status="failed",

                            error_message=(
                                result.get(
                                    "error",
                                    "Publishing failed"
                                )
                            )
                        )

                except Exception as error:

                    print(
                        f"Error publishing {post_id}: "
                        f"{error}"
                    )

                    self.social_post_repository.update_post_status(

                        post_id=post_id,

                        status="failed",

                        error_message=str(error)
                    )

        except Exception as error:

            print(
                f"Scheduler error: {error}"
            )


    async def start(self):

        if self.is_running:

            print("Scheduler already running")

            return

        self.is_running = True

        print("Social post scheduler started")

        while self.is_running:

            await self.process_due_posts()

            # Check every minute
            await asyncio.sleep(60)


    def stop(self):

        self.is_running = False

        print("Social post scheduler stopped")