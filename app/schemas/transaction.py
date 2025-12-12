from pydantic import BaseModel, ConfigDict
from datetime import datetime
from datetime import datetime, date

class STransactionCreate(BaseModel):
    amount: float
    description: str | None = None
    category_id: int
    transaction_date: datetime

class STransactionResponse(BaseModel):
    id: int
    amount: float
    description: str | None
    transaction_date: datetime
    created_at: datetime
    category_id: int
    
    model_config = ConfigDict(from_attributes=True)