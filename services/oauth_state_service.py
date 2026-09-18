import secrets

from datetime import (
    datetime,
    timedelta,
    timezone
)

from repositories.oauth_state_repository import (
    OAuthStateRepository
)


class OAuthStateService:

    def __init__(self):

        self.repository = (
            OAuthStateRepository()
        )


    # -----------------------------------
    # CREATE STATE
    # -----------------------------------

    def create_state(
        self,
        user_id: str,
        brand_profile_id: str,
        platform: str
    ):

        state = secrets.token_urlsafe(32)

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(minutes=10)
        )

        state_data = {
            "state": state,

            "user_id": user_id,

            "brand_profile_id": (
                brand_profile_id
            ),

            "platform": platform,

            "expires_at": (
                expires_at.isoformat()
            )
        }

        self.repository.create_state(
            state_data
        )

        return state


    # -----------------------------------
    # VALIDATE STATE
    # -----------------------------------

    def validate_state(
        self,
        state: str,
        platform: str
    ):

        states = (
            self.repository.get_state(state)
        )

        if not states:

            return None

        state_data = states[0]

        # -----------------------------------
        # PLATFORM VALIDATION
        # -----------------------------------

        if state_data["platform"] != platform:

            return None

        # -----------------------------------
        # EXPIRATION VALIDATION
        # -----------------------------------

        expires_at = datetime.fromisoformat(
            state_data["expires_at"]
        )

        now = datetime.now(timezone.utc)

        if now > expires_at:

            self.repository.delete_state(
                state
            )

            return None

        # -----------------------------------
        # ONE-TIME USE
        # -----------------------------------

        self.repository.delete_state(
            state
        )

        return state_data