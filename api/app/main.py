import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from .database import Base, engine, get_db
from .models import Expense
from .schemas import ExpenseCreate, ExpenseUpdate, ExpenseOut

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="Expense Tracker API",
    description="Expense management REST API",
    version="1.0.0",
    lifespan=lifespan
)

def check_api_key(x_api_key: str | None = Header(default=None)):
    expected = os.getenv("API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/api/expenses", response_model=list[ExpenseOut],
         tags=["Expenses"], dependencies=[Depends(check_api_key)])
def list_expenses(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    return db.scalars(
        select(Expense)
        .order_by(Expense.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

@app.post("/api/expenses", response_model=ExpenseOut, status_code=201,
          tags=["Expenses"], dependencies=[Depends(check_api_key)])
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    item = Expense(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/expenses/summary", tags=["Expenses"],
         dependencies=[Depends(check_api_key)])
def summary(db: Session = Depends(get_db)):
    return {
        "expense_count": db.scalar(select(func.count(Expense.id))),
        "total_amount": db.scalar(select(func.coalesce(func.sum(Expense.amount), 0)))
    }

@app.get("/api/expenses/{expense_id}", response_model=ExpenseOut,
         tags=["Expenses"], dependencies=[Depends(check_api_key)])
def get_expense(expense_id: int, db: Session = Depends(get_db)):
    item = db.get(Expense, expense_id)
    if not item:
        raise HTTPException(404, "Expense not found")
    return item

@app.patch("/api/expenses/{expense_id}", response_model=ExpenseOut,
           tags=["Expenses"], dependencies=[Depends(check_api_key)])
def update_expense(expense_id: int, payload: ExpenseUpdate,
                   db: Session = Depends(get_db)):
    item = db.get(Expense, expense_id)
    if not item:
        raise HTTPException(404, "Expense not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item

@app.delete("/api/expenses/{expense_id}", status_code=204,
            tags=["Expenses"], dependencies=[Depends(check_api_key)])
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    item = db.get(Expense, expense_id)
    if not item:
        raise HTTPException(404, "Expense not found")
    db.delete(item)
    db.commit()
    return Response(status_code=204)
