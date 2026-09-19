import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class SupabaseStorageService:

    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY")

        if not url:
            raise ValueError("SUPABASE_URL is not configured")

        if not key:
            raise ValueError("SUPABASE_SERVICE_KEY is not configured")

        self.client: Client = create_client(
            url,
            key
        )

        self.bucket = "generated-content"

    def get_social_post(self, post_id: str) -> dict:

        response = (
            self.client
            .table("social_posts")
            .select("*")
            .eq("id", post_id)
            .single()
            .execute()
        )

        if not response.data:
            raise ValueError(
                f"Social post not found: {post_id}"
            )

        return response.data

    def upload_image(
        self,
        local_path: str,
        storage_path: str
    ) -> str:

        file_path = Path(local_path)

        with open(file_path, "rb") as file:
            self.client.storage \
                .from_(self.bucket) \
                .upload(
                    path=storage_path,
                    file=file,
                    file_options={
                        "content-type": "image/png",
                        "cache-control": "3600",
                        "upsert": "true"
                    }
                )

        return storage_path

    def update_post_image(
        self,
        post_id: str,
        image_path: str
    ) -> dict:

        response = (
            self.client
            .table("social_posts")
            .update({
                "image_url": image_path
            })
            .eq("id", post_id)
            .execute()
        )

        if not response.data:
            raise ValueError(
                f"Could not update social post: {post_id}"
            )

        return response.data[0]

    def create_image_signed_url(
        self,
        storage_path: str,
        expires_in: int = 3600
    ) -> str:
    
        response = (
            self.client
            .storage
            .from_(self.bucket)
            .create_signed_url(
                storage_path,
                expires_in
            )
        )
    
        return response["signedURL"]