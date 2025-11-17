from sqlalchemy import Column, String, ForeignKey, DateTime, Integer, Float
from database import Base  # Import the 'Base' you just made

class Company(Base):
    __tablename__ = "companies"

    symbol = Column(String, primary_key=True, index=True)
    name = Column(String)

class DailyStockData(Base):
    __tablename__ = "daily_stock_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey("companies.symbol"))
    date = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Integer)
    daily_return = Column(Float)
    seven_day_ma = Column(Float)
    volatility_30d = Column(Float) # 30-day rolling volatility