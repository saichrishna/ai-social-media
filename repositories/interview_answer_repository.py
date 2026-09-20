from services.supabase_service import SupabaseService


class InterviewAnswerRepository:

    def __init__(self):
        self.supabase = SupabaseService().client


    def upsert_answers(self, answers: list[dict]):

        if not answers:
            return []

        response = (
            self.supabase
            .table("interview_answers")
            .upsert(
                answers,
                on_conflict="brand_profile_id,question_key"
            )
            .execute()
        )

        return response.data


    def get_answers(
        self,
        brand_profile_id: str,
        user_id: str
    ):

        response = (
            self.supabase
            .table("interview_answers")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )

        return response.data

    def list_content_by_user(self, user_id: str):

        response = (
            self.supabase
            .table("interview_answers")
            .select("brand_profile_id, answer_text")
            .eq("user_id", user_id)
            .execute()
        )

        return response.data or []
