from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List
import io

from . import crud, models, schemas, utils
from .database import SessionLocal, engine

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
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload an Excel file.")
    
    try:
        content = await file.read()
        transactions_to_create = utils.parse_excel_file(io.BytesIO(content))
        
        # To avoid duplicates in this simple version, we'll clear current ones or skip
        # For this prototype, we'll just add them.
        db_transactions = crud.bulk_create_transactions(db, transactions_to_create)
        return db_transactions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Backend MonArgent is running"}
