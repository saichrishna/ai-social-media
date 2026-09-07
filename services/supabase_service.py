import os

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class SupabaseService:

    def __init__(self):

        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

        if not supabase_url:
            raise ValueError("SUPABASE_URL is missing")

        if not supabase_key:
            raise ValueError("SUPABASE_SERVICE_KEY is missing")

        self.client: Client = create_client(
            supabase_url,
            supabase_key
        )