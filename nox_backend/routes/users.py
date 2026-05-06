from fastapi import APIRouter, Depends
from nox_backend.core.security import get_current_user

router = APIRouter()

def build_user_response(user: str):
    return {
        "username": user,
        "status": "active"
    }

@router.get("/users/me")
async def users_me(user: str = Depends(get_current_user)):
    return build_user_response(user)

@router.get("/user/me")
async def user_me(user: str = Depends(get_current_user)):
    return build_user_response(user)

@router.get("/me")
async def me(user: str = Depends(get_current_user)):
    return build_user_response(user)