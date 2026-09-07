from services.supabase_service import SupabaseService


class BrandProfileRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def create_profile(self, profile_data: dict):
        response = (
            self.supabase
            .table("brand_profiles")
            .insert(profile_data)
            .execute()
        )

        return response.data

    def get_profile(self, profile_id: str, user_id: str):
        response = (
            self.supabase
            .table("brand_profiles")
            .select("*")
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    def get_user_profiles(self, user_id: str):
        response = (
            self.supabase
            .table("brand_profiles")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    def update_profile(
        self,
        profile_id: str,
        user_id: str,
        profile_data: dict
    ):
        response = (
            self.supabase
            .table("brand_profiles")
            .update(profile_data)
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )

        return response.data

    def delete_profile(self, profile_id: str, user_id: str):
        response = (
            self.supabase
            .table("brand_profiles")
            .delete()
            .eq("id", profile_id)
            .eq("user_id", user_id)
            .execute()
        )


        return response.data