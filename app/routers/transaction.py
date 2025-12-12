from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.schemas.transaction import STransactionCreate, STransactionResponse, SStatsResponse

from app.database import get_session
from app.models import User
from app.routers.auth import get_current_user
from app.schemas.transaction import STransactionCreate, STransactionResponse
from app.dao.dao import TransactionDAO

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.post("/", response_model=STransactionResponse)
async def create_transaction(
    transaction_data: STransactionCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    new_transaction = await TransactionDAO.create(session, transaction_data, current_user)
    return new_transaction

@router.get("/report", response_model=list[STransactionResponse])
async def get_transaction_report(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    transactions = await TransactionDAO.get_report(session, current_user, start_date, end_date)
    return transactions

@router.get("/stats", response_model=SStatsResponse)
async def get_transaction_stats(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    stats = await TransactionDAO.get_stats(session, current_user, start_date, end_date)
    return stats