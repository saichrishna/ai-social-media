from fastapi import APIRouter, HTTPException

from models.user import UserCreateRequest
from repositories.user_repository import UserRepository


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


user_repository = UserRepository()


@router.post("/")
async def create_user(request: UserCreateRequest):

    try:

        user_data = request.model_dump()

        result = user_repository.create_user(
            user_data
        )

        return {
            "success": True,
            "user": result[0] if result else None
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


@router.get("/{user_id}")
async def get_user(user_id: str):

    result = user_repository.get_user(user_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "success": True,
        "user": result[0]
    }