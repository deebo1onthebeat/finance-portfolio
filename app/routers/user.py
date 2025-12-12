from fastapi import APIRouter, Depends
from app.schemas.user import SUserResponse
from app.models import User
from app.routers.auth import get_current_user 
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=SUserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user