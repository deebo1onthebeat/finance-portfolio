from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session
from app.schemas.user import SUserRegister, SUserResponse
from app.dao.dao import UserDAO

router = APIRouter(prefix="/auth", tags=["Auth & Users"])

@router.post("/register", response_model=SUserResponse)
async def register_user(
    user_data: SUserRegister,
    session: AsyncSession = Depends(get_session)
):
    # --- НАДЕЖНАЯ ПРОВЕРКА (ВСТАВЬ ЭТО) ---
    if len(user_data.password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пароль не может быть длиннее 72 символов"
        )
    # --- КОНЕЦ ПРОВЕРКИ ---

    # 1. Проверяем, есть ли такой email
    existing_user = await UserDAO.find_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    # 2. Создаем пользователя
    new_user = await UserDAO.create(session, user_data)

    # 3. Возвращаем ответ
    return new_user