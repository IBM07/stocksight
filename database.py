from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Define the database URL
# This tells SQLAlchemy to create a file named 'stock_data.db'
# in your project directory.
DATABASE_URL = "sqlite:///./stock_data.db"

# 2. Create the main 'engine'
# This is the primary interface to the database.
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
# Note: 'check_same_thread: False' is needed only for SQLite
# to allow FastAPI to use it correctly.

# 3. Create a 'SessionLocal' class
# This class is a "factory" for creating new database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create a 'Base' class
# Your data models in 'models.py' will inherit from this class.
Base = declarative_base()