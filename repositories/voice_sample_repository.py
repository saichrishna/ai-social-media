from services.supabase_service import SupabaseService


class VoiceSampleRepository:

    def __init__(self):
        self.supabase = SupabaseService().client


    def create_sample(self, sample_data: dict):

        response = (
            self.supabase
            .table("voice_samples")
            .insert(sample_data)
            .execute()
        )

        return response.data


    def get_samples(
        self,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("voice_samples")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data
