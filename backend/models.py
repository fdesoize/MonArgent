from sqlalchemy import Column, Integer, String, Float, Date
from .database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    label = Column(String)
    debit = Column(Float, nullable=True)
    credit = Column(Float, nullable=True)
    family = Column(String, default="Inconnu")
    category = Column(String, default="Inconnu")
    subcategory = Column(String, default="Inconnu")
    
    # Unique constraint could be added here based on date, label and amount 
    # but bank exports can have identical operations on the same day.
