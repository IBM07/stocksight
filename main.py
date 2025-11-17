from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
from functools import lru_cache # For caching
from pydantic import BaseModel # For response models
from typing import List # For response models

# Import your database components and models
from database import SessionLocal, engine, Base
import models

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize the FastAPI app
app = FastAPI(
    title="JarNox Stock Data Intelligence API",
    description="An API for fetching and analyzing stock market data."
)

# --- Define Response Models (Pydantic) ---
# This makes your /docs page clean and professional

class CompanyResponse(BaseModel):
    symbol: str
    name: str
    
    class Config:
        from_attributes = True # Renamed from orm_mode

class StockDataResponse(BaseModel):
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    daily_return: float
    seven_day_ma: float
    volatility_30d: float # Your new business metric
    
    class Config:
        from_attributes = True # Renamed from orm_mode


# --- Database Dependency with Caching ---
# This is the "HFT" bonus feature for performance

@lru_cache() # Caches the session factory
def get_db_session_maker():
    print("Creating new session maker") # You'll see this in your log ONCE
    return SessionLocal()

def get_db():
    db = get_db_session_maker()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.get("/", summary="API Health Check")
def read_root():
    return {"status": "API is running!"}

@app.get("/companies", 
         summary="Get All Available Companies", 
         response_model=List[CompanyResponse]) # <-- Updated
def get_companies(db: Session = Depends(get_db)):
    """
    Returns a list of all companies and their symbols
    available in the database.
    """
    companies = db.query(models.Company).all()
    if not companies:
        raise HTTPException(status_code=404, detail="No companies found")
    return companies

@app.get("/data/{symbol}", 
         summary="Get Last 30 Days of Stock Data", 
         response_model=List[StockDataResponse]) # <-- Updated
def get_stock_data(symbol: str, db: Session = Depends(get_db)):
    """
    Returns the last 30 days of trading data (OHLC, volume,
    and calculated metrics) for a given stock symbol.
    """
    symbol_upper = symbol.upper()
    if not symbol_upper.endswith((".NS", ".BO")):
         symbol_upper += ".NS"

    data = db.query(models.DailyStockData)\
        .filter(models.DailyStockData.symbol == symbol_upper)\
        .order_by(desc(models.DailyStockData.date))\
        .limit(30)\
        .all()
    
    if not data:
        raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
    return data

@app.get("/summary/{symbol}", summary="Get 52-Week Summary")
def get_stock_summary(symbol: str, db: Session = Depends(get_db)):
    """
    Returns the 52-week high, 52-week low, and 52-week
    average closing price for a given stock symbol.
    """
    symbol_upper = symbol.upper()
    if not symbol_upper.endswith((".NS", ".BO")):
         symbol_upper += ".NS"

    one_year_ago = datetime.now() - timedelta(days=365)

    summary = db.query(
        func.max(models.DailyStockData.high).label("52_week_high"),
        func.min(models.DailyStockData.low).label("52_week_low"),
        func.avg(models.DailyStockData.close).label("52_week_avg_close")
    ).filter(
        models.DailyStockData.symbol == symbol_upper,
        models.DailyStockData.date >= one_year_ago
    ).first()

    if not summary or summary[0] is None:
        raise HTTPException(status_code=404, detail=f"No summary data found for symbol {symbol}")
    
    return {
        "52_week_high": summary[0],
        "52_week_low": summary[1],
        "52_week_avg_close": round(summary[2], 2) # Rounding the avg
    }

# --- NEW BONUS ENDPOINT ---

@app.get("/compare", summary="(Bonus) Compare two stocks")
def compare_stocks(symbol1: str, symbol2: str, db: Session = Depends(get_db)):
    """
    Compares the last 90 days of closing prices for two given stock symbols.
    """
    ninety_days_ago = datetime.now() - timedelta(days=90)
    
    symbols = [symbol1, symbol2]
    response = {}

    for symbol in symbols:
        symbol_upper = symbol.upper()
        if not symbol_upper.endswith((".NS", ".BO")):
             symbol_upper += ".NS"
        
        data = db.query(models.DailyStockData.date, models.DailyStockData.close)\
            .filter(models.DailyStockData.symbol == symbol_upper)\
            .filter(models.DailyStockData.date >= ninety_days_ago)\
            .order_by(models.DailyStockData.date)\
            .all()
        
        if data:
            # Return data in a simple format for charting
            response[symbol] = {
                "dates": [row[0] for row in data],
                "closes": [row[1] for row in data]
            }
        else:
            response[symbol] = "No data found"

    return response
