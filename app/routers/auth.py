from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.dao.dao import UserDAO
from app.schemas.user import SUserRegister, SUserResponse, SUserLogin, STokenResponse
from app.auth import verify_password, create_access_token, verify_token
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth & Users"])


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=SUserResponse)
async def register_user(
    user_data: SUserRegister,
    session: AsyncSession = Depends(get_session)
):
    
    if len(user_data.password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пароль не может быть длиннее 72 символов"
        )

    existing_user = await UserDAO.find_by_email(session, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует"
        )

    new_user = await UserDAO.create(session, user_data)

    return new_user


@router.post("/login", response_model=STokenResponse)
async def login_for_access_token(
    form_data: SUserLogin,
    session: AsyncSession = Depends(get_session)
):
    user = await UserDAO.find_by_email(session, form_data.email)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session)
) -> User:
    email = verify_token(token)
    
    user = await UserDAO.find_by_email(session, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user