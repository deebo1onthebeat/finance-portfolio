from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import SUserRegister
from app.auth import get_password_hash

class UserDAO:
    @classmethod
    async def find_by_email(cls, session: AsyncSession, email: str):
        # Ищем пользователя по email
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, session: AsyncSession, user_in: SUserRegister):
        # 1. Превращаем пароль в хеш
        hashed_pw = get_password_hash(user_in.password)
        
        # 2. Создаем объект модели (готовим к записи в БД)
        new_user = User(
            email=user_in.email,
            hashed_password=hashed_pw
        )
        
        # 3. Сохраняем
        session.add(new_user)
        await session.commit()
        
        # 4. Обновляем объект, чтобы получить присвоенный ID
        await session.refresh(new_user)
        return new_user