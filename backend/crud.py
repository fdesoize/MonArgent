from sqlalchemy.orm import Session
from . import models, schemas
import logging

logger = logging.getLogger(__name__)

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transaction).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def bulk_create_transactions(db: Session, transactions: list[schemas.TransactionCreate]):
    logger.info(f"Attempting to bulk create {len(transactions)} transactions.")
    db_transactions = [models.Transaction(**t.dict()) for t in transactions]
    db.add_all(db_transactions)
    db.commit()
    logger.info(f"Successfully bulk created {len(db_transactions)} transactions.")
    return db_transactions
