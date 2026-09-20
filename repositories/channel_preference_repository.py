from services.supabase_service import SupabaseService


class ChannelPreferenceRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def upsert_preference(self, row: dict):

        response = (
            self.supabase
            .table("brand_channel_preferences")
            .upsert(
                row,
                on_conflict="brand_profile_id,platform"
            )
            .execute()
        )

        return response.data

    def list_preferences(
        self,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("brand_channel_preferences")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data
