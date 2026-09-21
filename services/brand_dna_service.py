from repositories.brand_profile_repository import BrandProfileRepository
from repositories.voice_study_repository import VoiceStudyRepository
from repositories.channel_preference_repository import (
    ChannelPreferenceRepository
)
from services.corpus_service import CorpusService


from services.brand_setup_status import MIN_MATERIAL_ITEMS

MIN_CORPUS_ITEMS = MIN_MATERIAL_ITEMS


class BrandDnaService:

    def __init__(self):
        self.brand_repository = BrandProfileRepository()
        self.corpus_service = CorpusService()
        self.study_repository = VoiceStudyRepository()
        self.channel_repository = ChannelPreferenceRepository()

    def load_owned_profile(
        self,
        profile_id: str,
        user_id: str
    ):

        rows = self.brand_repository.get_profile(
            profile_id,
            user_id
        )

        if not rows:
            return None

        return rows[0]

    def gather_corpus(
        self,
        brand_profile_id: str,
        user_id: str,
        *,
        topic: str = "",
    ) -> list[str]:

        self.corpus_service.backfill_from_legacy_if_empty(
            brand_profile_id,
            user_id,
        )

        return self.corpus_service.select_chunks_for_generation(
            brand_profile_id,
            user_id,
            topic=topic,
        )

    def corpus_item_count(
        self,
        brand_profile_id: str,
        user_id: str
    ) -> int:

        self.corpus_service.backfill_from_legacy_if_empty(
            brand_profile_id,
            user_id,
        )

        return self.corpus_service.material_count(
            brand_profile_id,
            user_id,
        )

    def has_minimum_corpus(
        self,
        brand_profile_id: str,
        user_id: str
    ) -> bool:

        return (
            self.corpus_item_count(
                brand_profile_id,
                user_id
            )
            >= MIN_CORPUS_ITEMS
        )

    def suggest_draft_topics(
        self,
        brand_profile_id: str,
        user_id: str
    ) -> list[dict]:

        self.corpus_service.backfill_from_legacy_if_empty(
            brand_profile_id,
            user_id,
        )

        items = self.corpus_service.list_items(
            brand_profile_id,
            user_id,
        )

        topics = []
        seen_themes: set[str | None] = set()

        for item in items:
            content = (item.get("content") or "").strip()
            if not content:
                continue
            theme = item.get("theme")
            if theme in seen_themes and theme:
                continue
            seen_themes.add(theme)
            topics.append({
                "topic": content[:160],
                "source": item.get("source") or "corpus_item",
                "question_key": theme,
            })
            if len(topics) >= 8:
                break

        return topics

    def build_generation_context(
        self,
        brand_profile: dict,
        brand_profile_id: str,
        user_id: str,
        platform: str,
        *,
        topic: str = "",
    ) -> str:

        sections = []

        sections.append(
            "BRAND PROMISE (explicit — do not contradict):"
        )
        sections.append(
            f"Who they help: {brand_profile.get('target_audience', '')}"
        )
        sections.append(
            f"Not for: {brand_profile.get('not_for', '')}"
        )
        sections.append(
            f"Services: {', '.join(brand_profile.get('services') or [])}"
        )
        sections.append(
            f"Forbidden topics: {', '.join(brand_profile.get('forbidden_topics') or [])}"
        )
        sections.append(
            f"Desired outcome: {brand_profile.get('desired_outcome', '')}"
        )

        corpus = self.gather_corpus(
            brand_profile_id,
            user_id,
            topic=topic,
        )

        if corpus:
            sections.append("\nUSER SOURCE MATERIAL (ground truth — do not invent beyond this):")
            for index, chunk in enumerate(corpus, start=1):
                sections.append(f"[{index}] {chunk}")

        studies = self.study_repository.get_latest_study(
            brand_profile_id,
            user_id
        )

        if studies:
            study = studies[0]
            keep = study.get("keep_items") or []
            raise_items = study.get("raise_items") or []
            if keep:
                sections.append("\nVOICE — KEEP (sound like them):")
                for item in keep:
                    sections.append(f"- {item}")
            if raise_items:
                sections.append("\nVOICE — RAISE (improve without erasing identity):")
                for item in raise_items:
                    sections.append(f"- {item}")

        prefs = self.channel_repository.list_preferences(
            brand_profile_id,
            user_id
        )

        platform_pref = next(
            (
                pref for pref in prefs
                if pref.get("platform") == platform
            ),
            None
        )

        sections.append(f"\nCHANNEL ROOM: {platform}")

        if platform_pref:
            if platform_pref.get("tone_notes"):
                sections.append(
                    f"Tone: {platform_pref['tone_notes']}"
                )
            if platform_pref.get("length_notes"):
                sections.append(
                    f"Length: {platform_pref['length_notes']}"
                )
            if platform_pref.get("hashtag_notes"):
                sections.append(
                    f"Hashtags: {platform_pref['hashtag_notes']}"
                )
        else:
            sections.append(self._default_room_rules(platform))

        sections.append(
            "\nHARD RULES: Do not invent products, offers, customer stories, "
            "or opinions not supported by source material above."
        )

        return "\n".join(sections).strip()

    def _default_room_rules(self, platform: str) -> str:

        defaults = {
            "linkedin": (
                "Shape: point of view + proof. Professional but human."
            ),
            "instagram": (
                "Shape: felt moment + tight caption. Visual-friendly."
            ),
            "facebook": (
                "Shape: conversation starter. Community tone."
            ),
        }

        return defaults.get(
            platform.lower(),
            "Shape: one clear idea, useful to the audience."
        )
