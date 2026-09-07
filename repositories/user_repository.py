from services.supabase_service import SupabaseService


class UserRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def create_user(self, user_data: dict):

        response = (
            self.supabase
            .table("users")
            .insert(user_data)
            .execute()
        )

        return response.data

    def get_user(self, user_id: str):

        response = (
            self.supabase
            .table("users")
            .select("*")
            .eq("id", user_id)
            .execute()
        )

        return response.data

    def get_user_by_email(self, email: str):

        response = (
            self.supabase
            .table("users")
            .select("*")
            .eq("email", email)
            .execute()
        )

        return response.data