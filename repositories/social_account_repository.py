from services.supabase_service import SupabaseService


class SocialAccountRepository:

    def __init__(self):

        self.supabase = (
            SupabaseService().client
        )


    # -----------------------------------
    # CREATE ACCOUNT
    # -----------------------------------

    def create_account(
        self,
        account_data: dict
    ):

        response = (
            self.supabase
            .table("social_accounts")
            .insert(account_data)
            .execute()
        )

        return response.data


    # -----------------------------------
    # GET SINGLE ACCOUNT
    # -----------------------------------

    def get_account(
        self,
        account_id: str,
        user_id: str | None = None
    ):

        query = (
            self.supabase
            .table("social_accounts")
            .select("*")
            .eq("id", account_id)
        )

        # Optional ownership check
        if user_id:

            query = query.eq(
                "user_id",
                user_id
            )

        response = query.execute()

        return response.data


    # -----------------------------------
    # GET USER ACCOUNTS
    # -----------------------------------

    def get_user_accounts(
        self,
        user_id: str
    ):

        response = (
            self.supabase
            .table("social_accounts")
            .select("*")
            .eq("user_id", user_id)
            .eq("is_active", True)
            .order(
                "created_at",
                desc=True
            )
            .execute()
        )

        return response.data


    # -----------------------------------
    # GET BRAND ACCOUNTS
    # -----------------------------------

    def get_brand_accounts(
        self,
        brand_profile_id: str,
        user_id: str | None = None
    ):

        query = (
            self.supabase
            .table("social_accounts")
            .select("*")
            .eq(
                "brand_profile_id",
                brand_profile_id
            )
            .eq("is_active", True)
        )

        if user_id:

            query = query.eq(
                "user_id",
                user_id
            )

        response = query.execute()

        return response.data


    # -----------------------------------
    # GET PLATFORM ACCOUNT
    # -----------------------------------

    def get_platform_account(
        self,
        user_id: str,
        brand_profile_id: str,
        platform: str
    ):

        response = (
            self.supabase
            .table("social_accounts")
            .select("*")
            .eq("user_id", user_id)
            .eq(
                "brand_profile_id",
                brand_profile_id
            )
            .eq("platform", platform.lower())
            .eq("is_active", True)
            .execute()
        )

        return response.data


    # -----------------------------------
    # UPDATE ACCOUNT
    # -----------------------------------

    def update_account(
        self,
        account_id: str,
        account_data: dict
    ):

        response = (
            self.supabase
            .table("social_accounts")
            .update(account_data)
            .eq("id", account_id)
            .execute()
        )

        return response.data


    # -----------------------------------
    # DEACTIVATE ACCOUNT
    # -----------------------------------

    def deactivate_account(
        self,
        account_id: str
    ):

        response = (
            self.supabase
            .table("social_accounts")
            .update({
                "is_active": False
            })
            .eq("id", account_id)
            .execute()
        )

        return response.data