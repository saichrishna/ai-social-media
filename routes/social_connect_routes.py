from fastapi import APIRouter, HTTPException

from services.social_providers.social_provider_factory import (
    SocialProviderFactory
)
from services.oauth_state_service import OAuthStateService

router = APIRouter(
    prefix="/api/social-connect",
    tags=["Social Connect"]
)

oauth_state_service = OAuthStateService()

# -----------------------------------
# START SOCIAL ACCOUNT CONNECTION
# -----------------------------------

@router.get("/connect/{platform}")
async def connect_social_account(
    platform: str,
    user_id: str,
    brand_profile_id: str
):

    try:

        provider = (
            SocialProviderFactory
            .get_provider(platform)
        )

        # Create secure random state

        state = (
            oauth_state_service.create_state(
            user_id=user_id,
            brand_profile_id=brand_profile_id,
            platform=platform
        )
    )

        authorization_url = (
            provider.get_authorization_url(
                state=state
            )
        )

        return {
            "success": True,
            "platform": platform,
            "authorization_url": authorization_url
        }

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )
    # -----------------------------------
# OAUTH CALLBACK
# -----------------------------------

@router.get("/callback/{platform}")
async def social_callback(
    platform: str,
    code: str,
    state: str
):

    try:

        # -----------------------------------
        # VALIDATE OAUTH STATE
        # -----------------------------------

        state_data = (
            oauth_state_service.validate_state(
                state = state,
                platform = platform
            )
        )

        if not state_data:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid or expired OAuth state"
                )
            )

        user_id = state_data["user_id"]

        brand_profile_id = (
            state_data["brand_profile_id"]
        )

        # -----------------------------------
        # GET PROVIDER
        # -----------------------------------

        provider = (
            SocialProviderFactory
            .get_provider(platform)
        )

        # -----------------------------------
        # EXCHANGE CODE
        # -----------------------------------

        token_data = (
            await provider.exchange_code(
                code=code
            )
        )

        # -----------------------------------
        # GET VERIFIED ACCOUNT
        # -----------------------------------

        accounts = (
            await provider.get_accounts(
                access_token=token_data[
                    "access_token"
                ]
            )
        )

        return {
            "success": True,
            "platform": platform,

            "user_id": user_id,

            "brand_profile_id": brand_profile_id,

            "accounts": accounts
        }

    except HTTPException:
        raise

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )