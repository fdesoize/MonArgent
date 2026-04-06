import logging
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io

from . import crud, models, schemas, utils
from .database import SessionLocal, engine

import os

# Configure logging to write to both console and a file
log_file_path = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MonArgent API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/transactions/", response_model=List[schemas.Transaction])
def read_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = crud.get_transactions(db, skip=skip, limit=limit)
    return transactions

@app.delete("/transactions/")
def delete_all_transactions(db: Session = Depends(get_db)):
    db.query(models.Transaction).delete()
    db.commit()
    return {"message": "Toutes les transactions ont été supprimées."}

@app.post("/upload/", response_model=List[schemas.Transaction])
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    logger.info(f"Received file upload request for file: {file.filename}")
    if not file.filename.endswith(('.xlsx', '.xls')):
        logger.warning(f"Invalid file format uploaded: {file.filename}. Expected .xlsx or .xls.")
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    try:
        logger.info(f"Reading content of file: {file.filename}")
        content = await file.read()
        logger.info(f"File {file.filename} content read successfully. Size: {len(content)} bytes.")

        logger.info(f"Parsing Excel file: {file.filename}")
        transactions_to_create = utils.parse_excel_file(io.BytesIO(content))
        logger.info(f"Successfully parsed {len(transactions_to_create)} transactions from {file.filename}.")
        
        logger.info(f"Bulk creating transactions in database.")
        db_transactions = crud.bulk_create_transactions(db, transactions_to_create)
        logger.info(f"Successfully created {len(db_transactions)} transactions in the database.")
        return db_transactions
    except HTTPException:
        # Re-raise HTTPExceptions as they are expected errors
        raise
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend MonArgent is running"}
