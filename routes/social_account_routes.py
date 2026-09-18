from fastapi import APIRouter, HTTPException

from repositories.social_account_repository import (
    SocialAccountRepository
)


router = APIRouter(
    prefix="/api/social-accounts",
    tags=["Social Accounts"]
)


social_account_repository = (
    SocialAccountRepository()
)


# -----------------------------------
# GET USER SOCIAL ACCOUNTS
# -----------------------------------

@router.get("/user/{user_id}")
async def get_user_social_accounts(
    user_id: str
):

    try:

        accounts = (
            social_account_repository
            .get_user_accounts(user_id)
        )

        return {
            "success": True,
            "accounts": accounts
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# -----------------------------------
# GET BRAND SOCIAL ACCOUNTS
# -----------------------------------

@router.get("/brand/{brand_profile_id}")
async def get_brand_social_accounts(
    brand_profile_id: str,
    user_id: str
):

    try:

        accounts = (
            social_account_repository
            .get_brand_accounts(
                brand_profile_id=brand_profile_id,
                user_id=user_id
            )
        )

        return {
            "success": True,
            "accounts": accounts
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# -----------------------------------
# GET SINGLE SOCIAL ACCOUNT
# -----------------------------------

@router.get("/{account_id}")
async def get_social_account(
    account_id: str,
    user_id: str
):

    try:

        accounts = (
            social_account_repository
            .get_account(
                account_id=account_id,
                user_id=user_id
            )
        )

        if not accounts:

            raise HTTPException(
                status_code=404,
                detail="Social account not found"
            )

        return {
            "success": True,
            "account": accounts[0]
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# -----------------------------------
# DISCONNECT SOCIAL ACCOUNT
# -----------------------------------

@router.delete("/{account_id}")
async def disconnect_social_account(
    account_id: str,
    user_id: str
):

    try:

        # Verify ownership first

        accounts = (
            social_account_repository
            .get_account(
                account_id=account_id,
                user_id=user_id
            )
        )

        if not accounts:

            raise HTTPException(
                status_code=404,
                detail="Social account not found"
            )

        result = (
            social_account_repository
            .deactivate_account(account_id)
        )

        return {
            "success": True,
            "message": "Social account disconnected",
            "account": (
                result[0]
                if result
                else None
            )
        }

    except HTTPException:
        raise

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )