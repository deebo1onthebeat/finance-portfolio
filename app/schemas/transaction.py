from pydantic import BaseModel, ConfigDict
from datetime import datetime
from enum import Enum

# (Enum)
class TransactionType(str, Enum):
    expense = "expense"  # Расход
    income = "income"    # Доход

# Схема для создания
class STransactionCreate(BaseModel):
    amount: float
    description: str | None = None
    category_id: int
    transaction_date: datetime
    type: TransactionType 
class STransactionResponse(BaseModel):
    id: int
    amount: float
    description: str | None
    transaction_date: datetime
    created_at: datetime
    category_id: int
    type: TransactionType 
    
    model_config = ConfigDict(from_attributes=True)