from pydantic import BaseModel
from datetime import date
from typing import Optional

class TransactionBase(BaseModel):
    date: date
    label: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    family: Optional[str] = "Inconnu"
    category: Optional[str] = "Inconnu"
    subcategory: Optional[str] = "Inconnu"

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int

    class Config:
        from_attributes = True
