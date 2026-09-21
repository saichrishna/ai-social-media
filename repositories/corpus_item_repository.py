from services.supabase_service import SupabaseService


class CorpusItemRepository:

    def __init__(self):
        self.supabase = SupabaseService().client

    def insert_items(self, rows: list[dict]):

        if not rows:
            return []

        response = (
            self.supabase
            .table("corpus_items")
            .insert(rows)
            .execute()
        )

        return response.data or []

    def list_items(
        self,
        brand_profile_id: str,
        user_id: str,
        *,
        limit: int | None = None,
    ):

        query = (
            self.supabase
            .table("corpus_items")
            .select("*")
            .eq("brand_profile_id", brand_profile_id)
            .eq("user_id", user_id)
            .order("created_at", desc=True)
        )

        if limit is not None:
            query = query.limit(limit)

        response = query.execute()

        return response.data or []

    def count_items(
        self,
        brand_profile_id: str,
        user_id: str,
    ) -> int:

        rows = self.list_items(
            brand_profile_id,
            user_id,
        )
        return len([
            row for row in rows
            if (row.get("content") or "").strip()
        ])

    def list_counts_by_user(self, user_id: str) -> dict[str, int]:

        response = (
            self.supabase
            .table("corpus_items")
            .select("brand_profile_id, content")
            .eq("user_id", user_id)
            .execute()
        )

        counts: dict[str, int] = {}

        for row in response.data or []:
            if not (row.get("content") or "").strip():
                continue
            profile_id = str(row.get("brand_profile_id") or "")
            if not profile_id:
                continue
            counts[profile_id] = counts.get(profile_id, 0) + 1

        return counts
