from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.models import User, Category, Transaction
from app.schemas.user import SUserRegister
from app.schemas.category import SCategoryCreate
from app.schemas.transaction import STransactionCreate
from app.auth import get_password_hash

class UserDAO:
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


class CategoryDAO:
    @classmethod
    async def create(cls, session: AsyncSession, category_in: SCategoryCreate, user: User):
        new_category = Category(name=category_in.name, user_id=user.id)
        session.add(new_category)
        await session.commit()
        await session.refresh(new_category)
        return new_category

    @classmethod
    async def find_all_by_user(cls, session: AsyncSession, user: User):
        query = select(Category).where(Category.user_id == user.id)
        result = await session.execute(query)
        return result.scalars().all()
        

class TransactionDAO:
    @classmethod
    async def create(cls, session: AsyncSession, transaction_in: STransactionCreate, user: User):
        new_transaction = Transaction(
            amount=transaction_in.amount,
            description=transaction_in.description,
            category_id=transaction_in.category_id,
            transaction_date=transaction_in.transaction_date,
            user_id=user.id,
            type=transaction_in.type # <-- ВАЖНО: Сохраняем тип (income/expense)
        )
        session.add(new_transaction)
        await session.commit()
        await session.refresh(new_transaction)
        return new_transaction
    
    @classmethod
    async def get_report(cls, session: AsyncSession, user: User, start_date: date, end_date: date):
        """Возвращает список транзакций за период."""
        query = select(Transaction).where(
            and_(
                Transaction.user_id == user.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        result = await session.execute(query)
        return result.scalars().all()