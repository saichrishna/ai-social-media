from repositories.brand_profile_repository import BrandProfileRepository
from repositories.voice_sample_repository import VoiceSampleRepository
from repositories.interview_answer_repository import (
    InterviewAnswerRepository
)
from repositories.voice_study_repository import VoiceStudyRepository
from repositories.channel_preference_repository import (
    ChannelPreferenceRepository
)


MIN_CORPUS_ITEMS = 3


class BrandDnaService:

    def __init__(self):
        self.brand_repository = BrandProfileRepository()
        self.sample_repository = VoiceSampleRepository()
        self.answer_repository = InterviewAnswerRepository()
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
        user_id: str
    ) -> list[str]:

        samples = self.sample_repository.get_samples(
            brand_profile_id,
            user_id
        )

        answers = self.answer_repository.get_answers(
            brand_profile_id,
            user_id
        )

        chunks: list[str] = []

        for sample in samples:
            content = (sample.get("content") or "").strip()
            if content:
                chunks.append(content)

        for answer in answers:
            text = (answer.get("answer_text") or "").strip()
            if text:
                chunks.append(text)

        return chunks

    def corpus_item_count(
        self,
        brand_profile_id: str,
        user_id: str
    ) -> int:

        return len(self.gather_corpus(
            brand_profile_id,
            user_id
        ))

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

        answers = self.answer_repository.get_answers(
            brand_profile_id,
            user_id
        )

        topics = []

        for answer in answers:
            text = (answer.get("answer_text") or "").strip()
            if not text:
                continue
            topics.append({
                "topic": text[:160],
                "source": "interview_answer",
                "question_key": answer.get("question_key")
            })

        if topics:
            return topics[:8]

        samples = self.sample_repository.get_samples(
            brand_profile_id,
            user_id
        )

        for sample in samples:
            content = (sample.get("content") or "").strip()
            if not content:
                continue
            first_line = content.split("\n")[0][:160]
            topics.append({
                "topic": first_line,
                "source": "voice_sample",
                "question_key": None
            })

        return topics[:8]

    def build_generation_context(
        self,
        brand_profile: dict,
        brand_profile_id: str,
        user_id: str,
        platform: str
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
            user_id
        )

        if corpus:
            sections.append("\nUSER SOURCE MATERIAL (ground truth — do not invent beyond this):")
            for index, chunk in enumerate(corpus[:12], start=1):
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
