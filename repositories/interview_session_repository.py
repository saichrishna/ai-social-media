from datetime import datetime, timezone

from services.supabase_service import SupabaseService


class InterviewSessionRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def create_session(self, row: dict):

        response = (
            self.supabase
            .table("interview_sessions")
            .insert(row)
            .execute()
        )

        return response.data

    def get_session(
        self,
        session_id: str,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("interview_sessions")
            .select("*")
            .eq("id", session_id)
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    def list_recent_sessions(
        self,
        brand_profile_id: str,
        user_id: str,
        *,
        limit: int = 10,
    ):

        response = (
            self.supabase
            .table("interview_sessions")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .limit(limit)
            .execute()
        )

        return response.data or []

    def get_active_session(
        self,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("interview_sessions")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .eq("status", "in_progress")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return response.data

    def update_session(
        self,
        session_id: str,
        patch: dict
    ):

        patch = {
            **patch,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

        response = (
            self.supabase
            .table("interview_sessions")
            .update(patch)
            .eq("id", session_id)
            .execute()
        )

        return response.data
