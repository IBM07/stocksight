import yfinance as yf
import pandas as pd
from database import SessionLocal, engine, Base  # Import from your database.py
from models import Company, DailyStockData      # Import from your models.py

# Your list of tickers
TICKERS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "LT.NS", "SBIN.NS", "AXISBANK.NS", "WIPRO.NS", "TECHM.NS",
    "MARUTI.NS", "HINDUNILVR.NS", "ITC.NS", "BHARTIARTL.NS", "ASIANPAINT.NS"
]

# Create a session
session = SessionLocal()

# Create the tables (this is safe to run multiple times)
Base.metadata.create_all(bind=engine)

try:
    # --- This is your main FTL loop ---
    for ticker in TICKERS:
        
        existing_company = session.query(Company).filter_by(symbol=ticker).first()
        if existing_company:
            print(f"Skipping {ticker}, already in database.")
            continue
            
        print(f"Processing {ticker}...")

        # 1. FETCH
        data_df = yf.download(ticker, period="5y")
        
        if data_df.empty:
            print(f"No data found for {ticker}, skipping.")
            continue
            
        # --- THE FINAL FIX: CORRECT ORDER OF OPERATIONS ---
        
        # 1. Move 'Date' from the INDEX to a COLUMN
        data_df.reset_index(inplace=True) 
        
        # 2. Flatten MultiIndex columns (if they exist)
        # Columns might now be ['Date', ('Open', ''), ('High', '')]
        if isinstance(data_df.columns, pd.MultiIndex):
            new_cols = []
            for col in data_df.columns:
                if isinstance(col, tuple):
                    new_cols.append(col[0]) # Get 'Open' from ('Open', '')
                else:
                    new_cols.append(col) # Keep 'Date'
            data_df.columns = new_cols
            
        # 3. NOW, standardize ALL columns to lowercase
        data_df.columns = data_df.columns.str.lower()
        
        # 2. TRANSFORM
        data_df.dropna(inplace=True)

        # Check for 'date' or 'datetime' (now reliably lowercase)
        date_col = 'date'
        if 'datetime' in data_df.columns:
            date_col = 'datetime'

        # Use lowercase 'close' and 'open' for all calculations
        data_df['daily_return'] = (data_df['close'] - data_df['open']) / data_df['open']
        data_df['seven_day_ma'] = data_df['close'].rolling(window=7).mean()
        data_df['volatility_30d'] = data_df['daily_return'].rolling(window=30).std()

        data_df.dropna(inplace=True) # Drop NaNs from rolling average

        # 3. LOAD
        try:
            company_info = yf.Ticker(ticker).info
            company_name = company_info.get('longName', ticker.split('.')[0])
        except Exception:
            company_name = ticker.split('.')[0] # Fallback
            
        company = Company(symbol=ticker, name=company_name)
        session.add(company)
        
        data_to_insert = []
        # Use lowercase keys for all row access
        for index, row in data_df.iterrows():
            stock_data = DailyStockData(
                symbol=ticker,
                date=row[date_col].to_pydatetime(), 
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close']),
                volume=int(row['volume']),
                daily_return=float(row['daily_return']),
                seven_day_ma=float(row['seven_day_ma']),
                volatility_30d=float(row['volatility_30d'])
            )
            data_to_insert.append(stock_data)
        
        session.bulk_save_objects(data_to_insert)
        session.commit()
        print(f"Successfully loaded data for {ticker}.")

    print("All tickers processed successfully.")

finally:
    session.close()
    print("Database session closed.")