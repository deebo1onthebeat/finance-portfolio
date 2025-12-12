from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Category # Добавь Category
from app.schemas.user import SUserRegister
from app.schemas.category import SCategoryCreate # Добавь SCategoryCreate
from app.auth import get_password_hash

class UserDAO:
    # ... тут твой старый код для UserDAO ...
    @classmethod
    async def find_by_email(cls, session: AsyncSession, email: str):
        query = select(User).where(User.email == email)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, session: AsyncSession, user_in: SUserRegister):
        hashed_pw = get_password_hash(user_in.password)
        new_user = User(email=user_in.email, hashed_password=hashed_pw)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

# --- НОВЫЙ КЛАСС ---
class CategoryDAO:
    @classmethod
    async def create(cls, session: AsyncSession, category_in: SCategoryCreate, user: User):
        # Создаем категорию с привязкой к пользователю
        new_category = Category(name=category_in.name, user_id=user.id)
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)
        return new_category

    @classmethod
    async def find_all_by_user(cls, session: AsyncSession, user: User):
        # Находим все категории, принадлежащие пользователю
        query = select(Category).where(Category.user_id == user.id)
        result = await session.execute(query)
        return result.scalars().all()