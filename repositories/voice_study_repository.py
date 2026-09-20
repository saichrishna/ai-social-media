from services.supabase_service import SupabaseService


class VoiceStudyRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def create_study(self, row: dict):

        response = (
            self.supabase
            .table("brand_voice_studies")
            .insert(row)
            .execute()
        )

        return response.data

    def get_latest_study(
        self,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("brand_voice_studies")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        return response.data
