from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date

from app.models import User, Category, Transaction
from app.schemas.user import SUserRegister
from app.schemas.category import SCategoryCreate, SCategoryUpdate
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

    # --- ВОТ ЭТОТ МЕТОД БЫЛ ПОТЕРЯН ---
    @classmethod
    async def update(cls, session: AsyncSession, category_id: int, category_in: SCategoryUpdate, user: User):
        # Ищем категорию, которая принадлежит именно этому юзеру
        query = select(Category).where(
            and_(Category.id == category_id, Category.user_id == user.id)
        )
        result = await session.execute(query)
        category = result.scalar_one_or_none()
        
        if not category:
            return None
        
        # Обновляем имя
        category.name = category_in.name
        await session.commit()
        await session.refresh(category)
        return category


class TransactionDAO:
    @classmethod
    async def create(cls, session: AsyncSession, transaction_in: STransactionCreate, user: User):
        new_transaction = Transaction(
            amount=transaction_in.amount,
            description=transaction_in.description,
            category_id=transaction_in.category_id,
            transaction_date=transaction_in.transaction_date,
            user_id=user.id,
            type=transaction_in.type
        )
        session.add(new_transaction)
        await session.commit()
        await session.refresh(new_transaction)
        return new_transaction
    
    @classmethod
    async def get_report(cls, session: AsyncSession, user: User, start_date: date, end_date: date):
        query = select(Transaction).where(
            and_(
                Transaction.user_id == user.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date
            )
        )
        result = await session.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_stats(cls, session: AsyncSession, user: User, start_date: date, end_date: date):
        # Доходы
        query_income = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == user.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.type == "income"
            )
        )
        result_income = await session.execute(query_income)
        income_val = result_income.scalar()
        total_income = float(income_val) if income_val else 0.0

        # Расходы
        query_expense = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.user_id == user.id,
                Transaction.transaction_date >= start_date,
                Transaction.transaction_date <= end_date,
                Transaction.type == "expense"
            )
        )
        result_expense = await session.execute(query_expense)
        expense_val = result_expense.scalar()
        total_expense = float(expense_val) if expense_val else 0.0

        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense
        }

    @classmethod
    async def get_statistics(cls, session: AsyncSession, user: User, start_date: date, end_date: date):
        query = (
            select(
                Category.name,
                func.sum(Transaction.amount).label("total_amount")
            )
            .join(Category, Transaction.category_id == Category.id)
            .where(
                and_(
                    Transaction.user_id == user.id,
                    Transaction.transaction_date >= start_date,
                    Transaction.transaction_date <= end_date,
                    Transaction.type == "expense"
                )
            )
            .group_by(Category.name)
        )
        result = await session.execute(query)
        return result.all()