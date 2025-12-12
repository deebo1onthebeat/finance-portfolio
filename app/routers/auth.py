from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dao.dao import UserDAO
from app.schemas.user import SUserRegister, SUserResponse, SUserLogin, STokenResponse
from app.auth import verify_password, create_access_token, verify_token
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth & Users"])

# Эта схема говорит FastAPI, что нужно искать токен в заголовке Authorization: Bearer <token>
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=SUserResponse)
async def register_user(
    user_data: SUserRegister,
    session: AsyncSession = Depends(get_session)
):
    # Проверка длины пароля, чтобы избежать ошибки bcrypt
    if len(user_data.password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пароль не может быть длиннее 72 символов"
        )

    # Проверяем, есть ли такой email
    existing_user = await UserDAO.find_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    # Создаем пользователя
    new_user = await UserDAO.create(session, user_data)

    # Возвращаем ответ
    return new_user


@router.post("/login", response_model=STokenResponse)
async def login_for_access_token(
    form_data: SUserLogin,
    session: AsyncSession = Depends(get_session)
):
    # 1. Ищем пользователя в базе
    user = await UserDAO.find_by_email(session, form_data.email)

    # 2. Проверяем, что юзер существует и пароль верный
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Создаем JWT токен
    access_token = create_access_token(data={"sub": user.email})

    # 4. Возвращаем токен
    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    """
    Зависимость-"охранник": проверяет токен и возвращает пользователя из БД.
    """
    # 1. Расшифровываем токен, чтобы получить email
    email = verify_token(token)
    
    # 2. Находим пользователя в базе
    user = await UserDAO.find_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user