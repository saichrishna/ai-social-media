from fastapi import APIRouter, HTTPException

from repositories.brand_profile_repository import (
    BrandProfileRepository
)

from models.brand_profile_request import (
    BrandProfileRequest
)


router = APIRouter(
    prefix="/brand-profiles",
    tags=["Brand Profiles"]
)


brand_repository = BrandProfileRepository()


# -----------------------------------
# CREATE BRAND PROFILE
# -----------------------------------

@router.post("/")
async def create_brand_profile(
    profile: BrandProfileRequest
):

    profile_data = profile.model_dump()

    result = (
        brand_repository
        .create_profile(profile_data)
    )

    if not result:
        raise HTTPException(
            status_code=500,
            detail="Failed to create brand profile"
        )

    return {
        "success": True,
        "brand_profile": result[0]
    }

# -----------------------------------
# GET USER BRAND PROFILES
# -----------------------------------

@router.get("/user/{user_id}")
async def get_user_brand_profiles(
    user_id: str
):

    result = (
        brand_repository
        .get_user_profiles(user_id)
    )

    return {
        "success": True,
        "brand_profiles": result
    }


# -----------------------------------
# GET BRAND PROFILE
# -----------------------------------

@router.get("/{profile_id}")
async def get_brand_profile(
    profile_id: str
):

    result = (
        brand_repository
        .get_profile(profile_id)
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return {
        "success": True,
        "brand_profile": result[0]
    }




# -----------------------------------
# UPDATE BRAND PROFILE
# -----------------------------------

@router.put("/{profile_id}")
async def update_brand_profile(
    profile_id: str,
    profile: BrandProfileRequest
):

    result = (
        brand_repository
        .update_profile(
            profile_id,
            profile.model_dump()
        )
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return {
        "success": True,
        "brand_profile": result[0]
    }


# -----------------------------------
# DELETE BRAND PROFILE
# -----------------------------------

@router.delete("/{profile_id}")
async def delete_brand_profile(
    profile_id: str
):

    result = (
        brand_repository
        .delete_profile(profile_id)
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Brand profile not found"
        )

    return {
        "success": True,
        "message": "Brand profile deleted"
    }