from services.supabase_service import SupabaseService


class OAuthStateRepository:

    def __init__(self):

        self.supabase = (
            SupabaseService().client
        )


    def create_state(
        self,
        state_data: dict
    ):

        response = (
            self.supabase
            .table("oauth_states")
            .insert(state_data)
            .execute()
        )

        return response.data


    def get_state(
        self,
        state: str
    ):

        response = (
            self.supabase
            .table("oauth_states")
            .select("*")
            .eq("state", state)
            .execute()
        )

        return response.data


    def delete_state(
        self,
        state: str
    ):

        response = (
            self.supabase
            .table("oauth_states")
            .delete()
            .eq("state", state)
            .execute()
        )

        return response.data