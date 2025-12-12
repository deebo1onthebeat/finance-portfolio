from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date
from app.schemas.transaction import STransactionCreate, STransactionResponse, SStatsResponse
from fastapi.responses import StreamingResponse
from app.services.charts import generate_pie_chart

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

@router.get("/graph", response_class=StreamingResponse)
async def get_expenses_graph(
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    # 1. Получаем статистику (используем тот же метод DAO, что и раньше)
    stats_data = await TransactionDAO.get_statistics(session, current_user, start_date, end_date)
    
    # 2. Подготавливаем данные для графика (только расходы)
    # Нам нужен словарь: {"Еда": 500.0, "Такси": 300.0}
    chart_data = {}
    for item in stats_data:
        # Мы хотим рисовать только расходы, доходы на круговой диаграмме обычно не нужны
        # Но пока нарисуем всё, что вернет статистика
        if item.total_amount > 0: # Исключаем отрицательные значения если вдруг
             chart_data[item.name] = float(item.total_amount)
    
    if not chart_data:
        raise HTTPException(status_code=404, detail="Нет данных за этот период")

    # 3. Генерируем картинку
    image_buf = generate_pie_chart(chart_data)
    
    # 4. Отдаем как файл
    return StreamingResponse(image_buf, media_type="image/png")


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