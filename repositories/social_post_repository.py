from services.supabase_service import SupabaseService
from datetime import datetime, timezone

class SocialPostRepository:

    def __init__(self):
        self.supabase = SupabaseService().client


    def create_post(self, post_data: dict):

        response = (
            self.supabase
            .table("social_posts")
            .insert(post_data)
            .execute()
        )

        return response.data


    def get_post(self, post_id: str):

        response = (
            self.supabase
            .table("social_posts")
            .select("*")
            .eq("id", post_id)
            .execute()
        )

        return response.data


    def get_user_posts(
        self,
        user_id: str,
        status: str | None = None
    ):

        query = (
            self.supabase
            .table("social_posts")
            .select("*")
            .eq("user_id", user_id)
        )

        if status:
            query = query.eq("status", status)

        response = (
            query
            .order("created_at", desc=True)
            .execute()
        )

        return response.data


    def get_brand_posts(
        self,
        brand_profile_id: str
    ):

        response = (
            self.supabase
            .table("social_posts")
            .select("*")
            .eq(
                "brand_profile_id",
                brand_profile_id
            )
            .order("created_at", desc=True)
            .execute()
        )

        return response.data


    def update_post(
        self,
        post_id: str,
        post_data: dict
    ):

        response = (
            self.supabase
            .table("social_posts")
            .update(post_data)
            .eq("id", post_id)
            .execute()
        )

        return response.data


    def delete_post(
        self,
        post_id: str
    ):

        response = (
            self.supabase
            .table("social_posts")
            .delete()
            .eq("id", post_id)
            .execute()
        )

        return response.data

    def schedule_post(
    self,
    post_id: str,
    scheduled_at: str,
    timezone: str
):

        response = (
            self.supabase
            .table("social_posts")
            .update({
                "scheduled_at": scheduled_at,
                "timezone": timezone,
                "status": "scheduled"
            })
            .eq("id", post_id)
            .execute()
        )

        return response.data


    def get_due_posts(self):

        now = datetime.now(timezone.utc).isoformat()

        response = (
            self.supabase
            .table("social_posts")
            .select("*")
            .eq("status", "scheduled")
            .lte("scheduled_at", now)
            .order("scheduled_at")
            .execute()
        )

        return response.data

    def update_post_status(
    self,
    post_id: str,
    status: str,
    error_message: str | None = None
):

        update_data = {
            "status": status
        }

        if error_message is not None:
            update_data["error_message"] = error_message

        response = (
            self.supabase
            .table("social_posts")
            .update(update_data)
            .eq("id", post_id)
            .execute()
        )

        return response.data

    def mark_post_published(
    self,
    post_id: str,
    external_post_id: str | None = None
):

        published_at = (
            datetime.now(timezone.utc).isoformat()
        )
    
        response = (
            self.supabase
            .table("social_posts")
            .update({
                "status": "published",
                "published_at": published_at,
                "external_post_id": external_post_id,
                "error_message": None
            })
            .eq("id", post_id)
            .execute()
        )
    
        return response.data