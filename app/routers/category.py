from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.models import User
from app.routers.auth import get_current_user 
from app.schemas.category import SCategoryCreate, SCategoryResponse
from app.dao.dao import CategoryDAO

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.post("/", response_model=SCategoryResponse)
async def create_category(
    category_data: SCategoryCreate,
    current_user: User = Depends(get_current_user), 
    session: AsyncSession = Depends(get_session)
):
    new_category = await CategoryDAO.create(session, category_data, current_user)
    return new_category

@router.get("/", response_model=list[SCategoryResponse])
async def get_user_categories(
    current_user: User = Depends(get_current_user), 
    session: AsyncSession = Depends(get_session)
):
    categories = await CategoryDAO.find_all_by_user(session, current_user)
    return categories